import datetime

from django import template

register = template.Library()


@register.filter
def get_custom_cell(mp, col):
    """Render a cell value for the custom report table."""
    today = datetime.date.today()
    ei = next(iter(mp.election_infos.all()), None)

    if col == 'name_en':      return mp.name_en or '—'
    if col == 'constituency': return ei.constituency.display_bn if ei and ei.constituency else '—'
    if col == 'party':        return ei.party.name_bn if ei and ei.party else '—'
    if col == 'age':
        if mp.dob:
            age = today.year - mp.dob.year - (
                (today.month, today.day) < (mp.dob.month, mp.dob.day)
            )
            return str(age)
        return '—'
    if col == 'blood_group':   return mp.blood_group.name_bn if mp.blood_group else '—'
    if col == 'gender':        return mp.gender.name_bn if mp.gender else '—'
    if col == 'religion':      return mp.religion.name_bn if mp.religion else '—'
    if col == 'division':
        return (mp.home_district.division.name_bn
                if mp.home_district and mp.home_district.division else '—')
    if col == 'district':      return mp.home_district.name_bn if mp.home_district else '—'
    if col == 'times_elected': return str(ei.times_elected) if ei else '—'
    if col == 'committee':
        return ', '.join(ca.committee.name_bn for ca in mp.committee_assignments.all()) or '—'
    if col == 'ministry':
        return ', '.join(ma.ministry.name_bn for ma in mp.ministry_assignments.all()) or '—'
    if col == 'profession':
        return ', '.join(p.name_bn for p in mp.professions_current.all()) or '—'
    if col == 'member_type':
        return 'সরাসরি নির্বাচিত' if mp.member_type == 'direct' else 'সংরক্ষিত (মহিলা)'
    if col in ('highest_edu_level', 'highest_degree', 'highest_subject'):
        edu = next((e for e in mp.educations.all() if e.education_level), None)
        if col == 'highest_edu_level':
            return edu.education_level.name_bn if edu else '—'
        if col == 'highest_degree':
            return edu.degree_title.name_bn if edu and edu.degree_title else '—'
        if col == 'highest_subject':
            return edu.major_subject.name_bn if edu and edu.major_subject else '—'
    if col == 'prof_qual':
        return ', '.join(pq.name_bn for pq in mp.professional_qualifications.all()) or '—'
    return '—'
