"""Duplicate detection + merge for the master reference tables.

Master data is entered by hand, so the same thing arrives twice under two
spellings — `রাষ্ট্র বিজ্ঞান` and `রাষ্ট্রবিজ্ঞান`, `ঢাকা  বোর্ড` (two spaces)
and `মাধ্যমিক ও উচ্চমাধ্যমিক শিক্ষা বোর্ড, ঢাকা`. Both then collect MP records.

Deactivating one of them does NOT unlink anything: the MP rows keep pointing at
the hidden row, so the same real-world value reads two different ways depending
on which report you open, and a filter on the surviving row silently loses those
MPs. The only correct fix is to *repoint* the data and then remove the loser —
which is what `merge()` does, in one transaction.

Nothing here is education-specific; it works for every master model that has
`name_bn` / `is_active`.
"""

import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher

from django.apps import apps
from django.db import transaction

# ── Scope ────────────────────────────────────────────────────────────────────
# A repeated name is only a duplicate WITHIN its parent. কালীগঞ্জ is a real
# upazila in four different districts and শিবগঞ্জ in two — comparing upazila
# names across the whole country reports 14 "duplicates" of which 1 is real.
NAME_SCOPE = {
    'master.Upazila': 'district_id',
    'master.District': 'division_id',
}

# Everything the loose key throws away before comparing. Catches the spacing and
# punctuation variants that make up most hand-entry duplicates:
#   এলএল.বি.  vs  এলএল.বি        ব্যারিস্টার অ্যাট ল  vs  ব্যারিস্টার-অ্যাট-ল
_LOOSE_STRIP = re.compile(r'[\s.\-‐-―_,;:()\[\]/\\\'"“”‘’]+')

SIMILARITY_THRESHOLD = 0.86


def norm(value):
    """Canonical form for comparison: NFC, trimmed, single-spaced, case-folded.

    NFC matters more than it looks — Bangla on this system is not byte
    normalised, so two visually identical strings can differ in code points and
    every `get_or_create` keyed on the raw text misses.
    """
    text = unicodedata.normalize('NFC', (value or '').strip())
    return re.sub(r'\s+', ' ', text).casefold()


def clean_name(value):
    """What we store: NFC + trimmed + single-spaced, case preserved."""
    text = unicodedata.normalize('NFC', (value or '').strip())
    return re.sub(r'\s+', ' ', text)


def loose_key(value):
    """`norm()` with all spacing and punctuation removed."""
    return _LOOSE_STRIP.sub('', norm(value))


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


# ── Usage ────────────────────────────────────────────────────────────────────

def _relations(model):
    """Reverse relations pointing at `model`, skipping unmanaged/hidden ones."""
    return [r for r in model._meta.related_objects if not r.hidden]


def usage(obj):
    """(total, [{'label', 'field', 'count'}]) — every row that references `obj`.

    This is the number the operator needs before merging: it says how much MP
    data moves, and it is the same number that must reach zero afterwards.
    """
    total = 0
    detail = []
    for rel in _relations(type(obj)):
        related = rel.related_model
        try:
            count = related._default_manager.filter(**{rel.field.name: obj}).count()
        except Exception:
            continue
        if count:
            total += count
            detail.append({
                'label': str(related._meta.verbose_name),
                'model': related._meta.label,
                'field': str(getattr(rel.field, 'verbose_name', rel.field.name)),
                'count': count,
            })
    return total, detail


# ── Detection ────────────────────────────────────────────────────────────────

def _scope_of(obj):
    field = NAME_SCOPE.get(obj._meta.label)
    return getattr(obj, field) if field else None


def find_duplicate_sets(model, loose=True):
    """Group rows of `model` that name the same thing.

    Two rows land in the same set when either their Bangla or their English name
    matches — a duplicate usually agrees on one language and diverges on the
    other (`জনপ্রশাসন` / `লোকপ্রশাসন` are both "Public Administration").
    Matching is transitive, so a three-way chain comes back as one set.
    """
    rows = list(model._default_manager.all())
    if len(rows) < 2:
        return []

    key = loose_key if loose else norm
    parent = {r.pk: r.pk for r in rows}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    buckets = defaultdict(list)
    for row in rows:
        scope = _scope_of(row)
        for value in (row.name_bn, getattr(row, 'name_en', '')):
            k = key(value)
            if k:
                buckets[(scope, k)].append(row.pk)
    for pks in buckets.values():
        for other in pks[1:]:
            union(pks[0], other)

    groups = defaultdict(list)
    for row in rows:
        groups[find(row.pk)].append(row)
    return [sorted(g, key=lambda r: r.pk) for g in groups.values() if len(g) > 1]


def find_similar(model, name_bn='', name_en='', exclude_pk=None, scope=None, limit=6):
    """Rows that look like the name being typed — the live add-form warning.

    Returns `(exact, near)`. `exact` means the canonical forms are equal, so the
    save is refused; `near` is only advice, because `মেডিসিন` / `চিকিৎসাবিজ্ঞান`
    are the same subject and no string metric will ever be sure of that.
    """
    targets = [(f, norm(v), loose_key(v))
               for f, v in (('name_bn', name_bn), ('name_en', name_en))
               if norm(v)]
    if not targets:
        return [], []

    qs = model._default_manager.all()
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    scope_field = NAME_SCOPE.get(model._meta.label)
    if scope_field:
        # An identically named upazila in another district is not a duplicate,
        # so an unset scope must not silently compare across all of them.
        scope_pk = getattr(scope, 'pk', scope)
        qs = qs.filter(**{scope_field: scope_pk}) if scope_pk else qs.none()

    exact, near = [], []
    for row in qs:
        best = 0.0
        hit_exact = False
        for field, n_target, l_target in targets:
            value = getattr(row, field, '')
            if norm(value) == n_target or loose_key(value) == l_target:
                hit_exact = True
                best = 1.0
                break
            best = max(best, similarity(l_target, loose_key(value)))
        if hit_exact:
            exact.append(row)
        elif best >= SIMILARITY_THRESHOLD:
            near.append((round(best, 3), row))

    near.sort(key=lambda pair: -pair[0])
    return exact, [row for _, row in near[:limit]]


def suggest_keeper(rows):
    """The row a merge should keep: active first, then most-used, then oldest id.

    Active comes before usage on purpose. Ranking by usage alone can elect a
    *deactivated* row as the survivor — on prod that briefly left "সমাজবিজ্ঞান"
    holding four MP records while hidden from every dropdown.
    Moving a few more references costs nothing; ending up with a survivor
    nobody can pick costs the whole point of the merge.
    """
    return sorted(rows, key=lambda r: (not r.is_active, -usage(r)[0], r.pk))[0]


def find_stranded(models=None):
    """Rows that are deactivated but still referenced by live data.

    This is the other half of the same problem as duplicates, and the half an
    operator cannot see at all: `is_active=False` hides the row from every
    picker while the records that already point at it keep pointing at it. On
    prod that included a TravelPurpose carrying 35 foreign tours. Either the row
    belongs back in the list, or its data belongs on another row — but silently
    hidden-and-in-use is never right.
    """
    out = []
    for model in (models or master_models()):
        for row in model._default_manager.filter(is_active=False):
            total, detail = usage(row)
            if total:
                out.append({'obj': row, 'model': model._meta.label,
                            'used': total, 'detail': detail})
    return out


# ── Merge ────────────────────────────────────────────────────────────────────

class MergeError(Exception):
    pass


@transaction.atomic
def merge(losers, winner, user=None, delete=True, ip=None):
    """Repoint every reference from `losers` onto `winner`, then drop them.

    Runs in one transaction: either all the MP data moves and the duplicates
    disappear, or nothing changes. `losers` must be the same model as `winner`.
    Returns a summary dict for the audit entry and the UI message.
    """
    model = type(winner)
    losers = [x for x in losers if x.pk != winner.pk]
    if not losers:
        raise MergeError('No duplicate selected to merge.')
    for loser in losers:
        if type(loser) is not model:
            raise MergeError('Cannot merge rows from two different tables.')

    moved = defaultdict(int)
    for loser in losers:
        for rel in _relations(model):
            related = rel.related_model
            field = rel.field
            qs = related._default_manager.filter(**{field.name: loser})
            key = f'{related._meta.label}.{field.name}'

            if field.many_to_many:
                # Reverse M2M: re-tag each row, and let `add` collapse the case
                # where it already carries both halves of the duplicate.
                for obj in qs:
                    manager = getattr(obj, field.name)
                    manager.remove(loser)
                    manager.add(winner)
                    moved[key] += 1
            else:
                count = qs.count()
                if count:
                    qs.update(**{field.name: winner})
                    moved[key] += count

    # Nothing may still point at a row we are about to delete.
    stranded = {l.pk: usage(l)[0] for l in losers}
    if any(stranded.values()):
        raise MergeError(f'References survived the merge: {stranded}')

    removed = []
    for loser in losers:
        removed.append({'pk': loser.pk, 'name_bn': loser.name_bn,
                        'name_en': getattr(loser, 'name_en', '')})
        if delete:
            loser.delete()
        else:
            loser.is_active = False
            loser.save(update_fields=['is_active'])

    summary = {
        'model': model._meta.label,
        'kept': {'pk': winner.pk, 'name_bn': winner.name_bn,
                 'name_en': getattr(winner, 'name_en', '')},
        'removed': removed,
        'moved': dict(moved),
        'deleted': delete,
    }
    _audit(model, winner, summary, user, ip)
    return summary


def _audit(model, winner, summary, user, ip):
    """Log the merge. `queryset.update()` fires no signals, so the rows that
    moved would otherwise leave no trace at all — and the reports cache keys off
    the audit table, so this is also what makes the merge visible immediately."""
    try:
        AuditLog = apps.get_model('reports', 'AuditLog')
        AuditLog.objects.create(
            user=user if getattr(user, 'pk', None) else None,
            app_label=model._meta.app_label,
            model_name=model._meta.model_name,
            object_id=str(winner.pk),
            object_repr=str(winner)[:300],
            action='UPDATE',
            changes={'merge': summary},
            ip_address=ip,
        )
    except Exception:
        pass  # never let audit failure roll back a good merge


# ── Model registry ───────────────────────────────────────────────────────────

def master_models():
    """Every master table that has a bilingual name — i.e. every one a duplicate
    can happen in. Read off the app registry so a new master model is covered
    the day it is added, with no list to remember to update."""
    out = []
    for model in apps.get_app_config('master').get_models():
        names = {f.name for f in model._meta.get_fields()}
        if 'name_bn' in names and 'is_active' in names:
            out.append(model)
    return sorted(out, key=lambda m: m._meta.verbose_name.lower())
