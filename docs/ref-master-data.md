# ref-master-data.md — Master Data Module & Accounts/Roles

---

## MASTER DATA MODULE — apps/master/

The primary admin interface for all reference/dropdown tables.
Full CRUD on every model. Soft delete (is_active=False) preserves FK integrity.

---

## MASTER DATA MENU

```
Master Data
├── Geography
│   ├── Divisions                    CRUD
│   ├── Districts                    CRUD
│   └── Upazilas                     CRUD
├── Constituencies                   CRUD  ← simple text entry (display_bn + display_en)
├── Parliament                       CRUD
├── Personal
│   ├── Religions                    CRUD
│   ├── Blood Groups                 CRUD
│   ├── Marital Status               CRUD
│   └── Genders                      CRUD
├── Professional
│   ├── Professions                  CRUD  ← current/previous occupation
│   └── Professional Qualifications  CRUD  ← Doctor/Engineer/Lawyer
├── Education
│   ├── Education Levels             CRUD  ← PSC/JSC/SSC/HSC/Graduation...
│   ├── Education Groups             CRUD  ← Science/Arts/Commerce
│   ├── Degree Names                 CRUD  ← BSc/MBBS/LLB/MA
│   ├── Subjects                     CRUD
│   ├── Institutions                 CRUD  ← Boards + Universities
│   └── Result Types                 CRUD  ← Division/GPA/CGPA/%
├── Political
│   └── Political Parties            CRUD
├── Ministry
│   ├── Ministries                   CRUD
│   └── Minister Types               CRUD  ← মন্ত্রী/প্রতিমন্ত্রী/উপমন্ত্রী
├── Committee
│   ├── Standing Committees          CRUD
│   └── Committee Positions          CRUD  ← সভাপতি/সদস্য
├── Institution
│   ├── Institutions                 CRUD  ← BUP/BUET etc.
│   └── Institution Roles            CRUD  ← Senate Member/Governor
├── Travel
│   ├── Countries                    CRUD
│   ├── Travel Types                 CRUD  ← Official/Personal/Legacy
│   └── Travel Purposes              CRUD  ← Hajj/Official Visit
└── Language
    ├── Foreign Languages            CRUD
    └── Proficiency Levels           CRUD
```

---

## GENERIC CRUD VIEW PATTERN

Every master data model uses this pattern:

```python
class MasterListView(LoginRequiredMixin, PermissionMixin, ListView):
    template_name = 'master/generic_list.html'
    # Features: search box, pagination, active/inactive toggle

class MasterCreateView(LoginRequiredMixin, PermissionMixin, CreateView):
    template_name = 'master/generic_form.html'

class MasterUpdateView(LoginRequiredMixin, PermissionMixin, UpdateView):
    template_name = 'master/generic_form.html'

class MasterDeactivateView(LoginRequiredMixin, PermissionMixin, View):
    """Soft delete — sets is_active=False. Hard delete only if no FK exists."""
```

---

## ACCOUNTS & ROLE SYSTEM — apps/accounts/

```python
class CustomUser(AbstractUser):
    role          = FK(Role, null=True)
    is_superadmin = BooleanField(default=False)
    full_name_bn  = CharField()
    full_name_en  = CharField()
    created_by    = FK('self', null=True)
    is_active     = BooleanField(default=True)

class Menu(Model):
    name_bn / name_en / icon / url_name / ordering / is_active

class SubMenu(Model):
    menu / name_bn / name_en / url_name / ordering / is_active

class Role(Model):
    name_bn / name_en / description_bn / description_en
    created_by / is_active

class RolePermission(Model):
    role       = FK(Role)
    submenu    = FK(SubMenu)
    can_view   = BooleanField(default=False)
    can_add    = BooleanField(default=False)
    can_edit   = BooleanField(default=False)
    can_delete = BooleanField(default=False)
    can_export = BooleanField(default=False)

    class Meta:
        unique_together = ['role', 'submenu']
```

**Middleware:**
```python
class RolePermissionMiddleware:
    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_superadmin:
            url_name = resolve(request.path).url_name
            submenu  = SubMenu.objects.filter(url_name=url_name).first()
            if submenu:
                perm = RolePermission.objects.filter(
                    role=request.user.role, submenu=submenu
                ).first()
                if not perm or not perm.can_view:
                    return HttpResponseForbidden()
        return self.get_response(request)
```

**Rules:**
- Superadmin bypasses ALL permission checks.
- Report export requires `can_export=True` in RolePermission.
- AUTH_USER_MODEL = `'accounts.CustomUser'`
