# ref-design.md — UI/UX Design Reference
# Source: login_page.jpg + System_Details_page.jpg

---

## COLOR PALETTE

```css
/* Primary — Parliament Teal (adapted from reference images) */
--mp-primary:        #0d9488;   /* teal-600  — buttons, active links, accents */
--mp-primary-dark:   #0f766e;   /* teal-700  — hover state */
--mp-primary-light:  #ccfbf1;   /* teal-100  — badge backgrounds, highlights */

/* Neutral */
--mp-bg:             #f8fafc;   /* slate-50  — page background */
--mp-surface:        #ffffff;   /* white     — cards, panels */
--mp-border:         #e2e8f0;   /* slate-200 — card borders, dividers */
--mp-text:           #0f172a;   /* slate-900 — primary text */
--mp-text-muted:     #64748b;   /* slate-500 — labels, captions */

/* Status */
--mp-success:        #16a34a;
--mp-warning:        #d97706;
--mp-danger:         #dc2626;
```

Bootstrap 5 override in `static/css/theme.css`:
```css
:root {
  --bs-primary:       #0d9488;
  --bs-primary-rgb:   13, 148, 136;
  --bs-body-bg:       #f8fafc;
  --bs-border-color:  #e2e8f0;
}
.btn-primary         { background-color: #0d9488; border-color: #0d9488; }
.btn-primary:hover   { background-color: #0f766e; border-color: #0f766e; }
.text-primary        { color: #0d9488 !important; }
.border-primary      { border-color: #0d9488 !important; }
```

---

## TYPOGRAPHY

```css
/* Stack — SolaimanLipi for Bangla, system-ui for English */
body {
  font-family: 'SolaimanLipi', 'Segoe UI', system-ui, sans-serif;
  font-size: 15px;
  color: #0f172a;
  line-height: 1.6;
}

h1 { font-size: 2rem;   font-weight: 700; }
h2 { font-size: 1.5rem; font-weight: 700; }
h3 { font-size: 1.25rem; font-weight: 600; }
h4 { font-size: 1.1rem;  font-weight: 600; }

.text-muted { color: #64748b; font-size: 0.875rem; }
.label      { font-size: 0.8125rem; color: #64748b; font-weight: 500; }
```

---

## LOGIN PAGE

**Layout:** Two-column split, 50/50.

```
┌─────────────────────────┬────────────────────────────┐
│   LEFT — white panel    │   RIGHT — image panel      │
│                         │                            │
│   [Parliament Logo]     │   [Parliament Building     │
│   [System Title bn/en]  │    full-bleed image]       │
│                         │                            │
│   ──────────────────    │   Overlay text at bottom:  │
│   [Username field]      │   "বাংলাদেশ জাতীয় সংসদ সচিবালয়"   │
│   [Password field]      │   "Bangladesh Parliament Secretariat"             │
│   [Remember me]                                      │
│   [Forgot Password?]    │                            │
│                         │                            │
│   [██ লগইন করুন ████]   │                            │
└─────────────────────────┴────────────────────────────┘
```

**Left panel specs:**
- White background, centered content, max-width 420px, padding 48px
- Logo: parliament emblem SVG/PNG, 72px height
- Title: `name_bn` bold 1.5rem, `name_en` muted 0.875rem below
- Divider line between title and form
- Inputs: floating label style (label shrinks on focus/fill)
- Password: show/hide toggle icon (right side)
- "Remember me" checkbox left + "পাসওয়ার্ড ভুলেছেন?" link right, same row
- Login button: full-width, `btn-primary`, 48px height, bold text
- No social login buttons (government system — username/password only)

**Right panel specs:**
- Full-bleed background image of Parliament House, Dhaka
- Dark gradient overlay: `linear-gradient(to top, rgba(0,0,0,0.7) 0%, transparent 60%)`
- Bottom text overlay: institution name in white, bold

**Floating label input CSS:**
```css
.form-floating > .form-control {
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  height: 52px;
  padding: 1rem 0.75rem 0.25rem;
}
.form-floating > .form-control:focus {
  border-color: #0d9488;
  box-shadow: 0 0 0 3px rgba(13,148,136,0.15);
}
.form-floating > label { color: #64748b; font-size: 0.875rem; }
```

---

## BASE LAYOUT (Authenticated Pages)

```
┌──────────────────────────────────────────────────────┐
│  TOPBAR  [☰] [Logo + System Name]      [Lang bn|en] [👤 User ▼]  │
├──────────┬───────────────────────────────────────────┤
│          │  BREADCRUMB                               │
│ SIDEBAR  │  ─────────────────────────────────────── │
│  240px   │                                           │
│          │  PAGE CONTENT AREA                        │
│ [Menu    │                                           │
│  items   │                                           │
│  with    │                                           │
│  icons]  │                                           │
│          │                                           │
└──────────┴───────────────────────────────────────────┘
```

**Topbar:**
- Height: 60px, white background, `border-bottom: 1px solid #e2e8f0`
- Left: hamburger toggle + logo (32px) + "সংসদ সদস্য তথ্য ব্যবস্থাপনা" bold
- Right: language toggle pill (বাং | EN) + user avatar + name + dropdown caret
- `box-shadow: 0 1px 4px rgba(0,0,0,0.06)`

**Sidebar:**
- Width: 240px (collapsed: 64px icon-only)
- Background: `#0f172a` (dark slate)
- Logo area top: 60px, teal accent bar left side on active item
- Menu items: icon (20px) + label, 44px height each, 8px border-radius
- Active item: `background: rgba(13,148,136,0.15)`, `color: #0d9488`, left border 3px teal
- Hover: `background: rgba(255,255,255,0.06)`
- Section headers: uppercase 10px, muted, letter-spacing 0.08em
- Footer: user initials avatar + name (small)

**Content area:**
- Background: `#f8fafc`
- Padding: 24px
- Max useful width: fluid within container

---

## CARDS

All content sections live inside cards. Inspired by the clean card panels in System_Details_page.jpg.

```css
.mp-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.mp-card-header {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  padding-bottom: 16px;
  margin-bottom: 20px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.mp-card-header .icon {
  width: 20px; height: 20px;
  color: #0d9488;
}
```

---

## KPI / STAT CARDS (Dashboard)

Inspired by the 4-column stats row in System_Details_page.jpg.

```
┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  [icon]       │  │  [icon]       │  │  [icon]       │  │  [icon]       │
│  350          │  │  42           │  │  12           │  │  48           │
│  মোট সদস্য  │  │  মন্ত্রী      │  │  কমিটি       │  │  বিদেশ সফর  │
└───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘
```

```css
.stat-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.stat-card .stat-icon {
  width: 40px; height: 40px;
  background: #ccfbf1;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #0d9488;
}
.stat-card .stat-value {
  font-size: 2rem; font-weight: 700; color: #0f172a; line-height: 1;
}
.stat-card .stat-label {
  font-size: 0.875rem; color: #64748b;
}
```

---

## BUTTONS

```css
/* Primary — teal fill */
.btn-primary {
  background: #0d9488; border: none; color: #fff;
  border-radius: 8px; font-weight: 600;
  padding: 0.5rem 1.25rem;
}
.btn-primary:hover { background: #0f766e; }

/* Secondary — outline */
.btn-outline-primary {
  border: 1.5px solid #0d9488; color: #0d9488; background: transparent;
  border-radius: 8px; font-weight: 600;
}
.btn-outline-primary:hover { background: #ccfbf1; }

/* Danger — soft red */
.btn-danger { background: #dc2626; border: none; border-radius: 8px; }

/* Icon buttons — small square */
.btn-icon {
  width: 34px; height: 34px; padding: 0;
  display: inline-flex; align-items: center; justify-content: center;
  border-radius: 8px;
}
```

---

## FORMS

**Field layout in forms:**
- Label above input (not inline), 12px margin between label and input
- Input height: 42px for single line, auto for textarea
- Border: `1.5px solid #e2e8f0`, radius `8px`
- Focus ring: `border-color: #0d9488`, `box-shadow: 0 0 0 3px rgba(13,148,136,0.12)`
- Required fields: asterisk in teal after label
- Error state: `border-color: #dc2626`, red helper text below
- Helptext: small muted text below input

**Multi-section MP form (tabs on top of content card):**
```
┌─────────────────────────────────────────────────────────┐
│  [১. সাধারণ] [২. নির্বাচন] [৩. পরিবার] [৪. শিক্ষা] … │  ← tab nav
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Section content in card below                          │
│                                                         │
│           [পূর্ববর্তী]    [সংরক্ষণ করুন]               │
└─────────────────────────────────────────────────────────┘
```

**Inline formset rows (Education, Children, etc.):**
```
┌──────┬────────────────────┬──────────────┬──────────────┬──────┐
│  #   │ Field 1            │ Field 2      │ Field 3      │ [×]  │
├──────┼────────────────────┼──────────────┼──────────────┼──────┤
│  ১   │ [input          ]  │ [select   ▼] │ [input    ]  │ [×]  │
│  ২   │ [input          ]  │ [select   ▼] │ [input    ]  │ [×]  │
└──────┴────────────────────┴──────────────┴──────────────┴──────┘
                                              [+ সারি যোগ করুন]
```

---

## TABLES (List Views)

Inspired by the clean, minimal table style visible in System_Details_page.jpg.

```
┌─────────────────────────────────────────────────────────────┐
│  [🔍 অনুসন্ধান...]   [ফিল্টার ▼]   [+ নতুন যোগ করুন]    │
├──────────────────────────────────────────────────────────────┤
│  #  │  নাম               │  আসন    │  দল      │  অ্যাকশন  │
├─────┼────────────────────┼──────────┼──────────┼───────────┤
│  ১  │  মোঃ সেলিম ভুইয়া │  ১২      │  BNP     │  [✏] [🗑] │
│  ২  │  ...               │  ...     │  ...     │  [✏] [🗑] │
├─────┴────────────────────┴──────────┴──────────┴───────────┤
│  ← পূর্ববর্তী   পৃষ্ঠা ১/৭   পরবর্তী →         ২৫ টি দেখাচ্ছে │
└─────────────────────────────────────────────────────────────┘
```

```css
.mp-table { width: 100%; border-collapse: separate; border-spacing: 0; }
.mp-table thead th {
  background: #f8fafc;
  font-size: 0.75rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
  color: #64748b;
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
}
.mp-table tbody td {
  padding: 14px 16px;
  border-bottom: 1px solid #f1f5f9;
  color: #0f172a;
  vertical-align: middle;
}
.mp-table tbody tr:hover { background: #f8fafc; }
.mp-table tbody tr:last-child td { border-bottom: none; }
```

---

## BADGES / STATUS PILLS

```css
.badge-active   { background: #dcfce7; color: #16a34a; border-radius: 20px; }
.badge-inactive { background: #fee2e2; color: #dc2626; border-radius: 20px; }
.badge-primary  { background: #ccfbf1; color: #0d9488; border-radius: 20px; }

/* Usage */
<span class="badge badge-active">সক্রিয়</span>
<span class="badge badge-inactive">নিষ্ক্রিয়</span>
```

---

## PAGE TITLES + BREADCRUMB

```html
<!-- Standard page header inside content area -->
<div class="d-flex align-items-center justify-content-between mb-4">
  <div>
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb mb-1" style="font-size:0.8125rem;">
        <li class="breadcrumb-item"><a href="#">হোম</a></li>
        <li class="breadcrumb-item"><a href="#">সংসদ সদস্য</a></li>
        <li class="breadcrumb-item active">তালিকা</li>
      </ol>
    </nav>
    <h4 class="mb-0 fw-bold">সংসদ সদস্য তালিকা</h4>
    <small class="text-muted">১৩তম জাতীয় সংসদ — ৩৫০ জন সদস্য</small>
  </div>
  <div class="d-flex gap-2">
    <button class="btn btn-outline-primary btn-sm">Excel</button>
    <button class="btn btn-outline-primary btn-sm">PDF</button>
    <button class="btn btn-primary btn-sm">+ নতুন যোগ করুন</button>
  </div>
</div>
```

---

## MP PROFILE / DETAIL PAGE LAYOUT

**CRITICAL: Tab order must follow the PDF form section order exactly.**
See `docs/ref-form-mapping.md` for complete field-by-field ordering within each tab.

```
┌──────────────────────────────────────────────────────────────────┐
│  [← তালিকায় ফিরুন]              [✏ সম্পাদনা] [🖨 প্রিন্ট]     │
├───────────────┬──────────────────────────────────────────────────┤
│  [Photo       │  ড. মুহাম্মদ ওসমান ফারুক                       │
│   120×150px]  │  DR. MUHAMMAD OSMAN FARRUK                       │
│               │  আসন: ১২ কিশোরগঞ্জ-১  |  BNP  |  MP: 013000101 │
├───────────────┴──────────────────────────────────────────────────┤
│ [১.সাধারণ][২.নির্বাচন][৩.স্বামী/স্ত্রী][৪.সন্তান][৫.শিক্ষা]  │
│ [৬.ঠিকানা][৭.ভাষা][৮.ব্যাংক][৯.কোভিড][১০.মন্ত্রণালয়]        │
│ [১১.কমিটি][১২.পূর্ববর্তী][১৩.সংগঠন][১৪.পুরস্কার][১৫.সমাজ]   │
│ [১৬.বিশেষ পদ][১৭.প্রকাশনা][১৮.বিদেশ ভ্রমণ]                   │
├──────────────────────────────────────────────────────────────────┤
│  Tab content card                                                │
└──────────────────────────────────────────────────────────────────┘
```

Tab numbering maps 1:1 to form section numbers (1–18).
Sections 19 (শখ) and 20 (অন্যান্য) are folded into Tab 1 at the bottom.

**Tab 1 — সাধারণ তথ্য — two-column grid layout (mirrors form's paired layout):**
```
[নাম (বাংলায়)                              ]  ← full width
[নাম (ইংরেজি বড় অক্ষর)                   ]  ← full width
[পিতার নাম (বাংলায়)                       ]  ← full width
[পিতার নাম (ইংরেজি বড় অক্ষর)            ]  ← full width
[মাতার নাম (বাংলায়)                       ]  ← full width
[মাতার নাম (ইংরেজি বড় অক্ষর)            ]  ← full width
[জন্ম তারিখ            ] [জাতীয় পরিচয়পত্র নং  ]  ← 2-col
[জন্মস্থান (জেলা)      ] [লিঙ্গ                 ]  ← 2-col
[নিজ জেলা              ] [বৈবাহিক অবস্থা        ]  ← 2-col
[জাতীয়তা              ] [ধর্ম                   ]  ← 2-col
[রক্তের গ্রুপ          ] [পেশা (বর্তমান)  ▼ M2M ]  ← 2-col
[পেশা (পূর্বের) ▼ M2M ] [টিআইএন                ]  ← 2-col
[পেশাদার যোগ্যতা ▼ M2M — full width, system addition]
── পাসপোর্ট ────────────── ── মুক্তিযুদ্ধ ──────────
[পাসপোর্ট নং          ] [মুক্তিযোদ্ধা ☐         ]
[ইস্যুর তারিখ         ] [মুক্তিযোদ্ধার সন্তান ☐ ]
[ইস্যুর স্থান         ] [নাতি-নাতনি ☐            ]
[মেয়াদোত্তীর্ণ তারিখ ]
── ছবি আপলোড (top right of card, form says attach photo) ─────────
── শখ (Section 19) ───────────────────────────────────────────────
[শখ (বাংলায়)                              ]
── অন্যান্য (Section 20) ─────────────────────────────────────────
[অন্যান্য তথ্য (বাংলায়)                  ]
```

Profile header card:
- Light teal gradient top strip (8px height)
- Photo: 120×150px, rounded 8px, `object-fit: cover`, border 2px white + shadow
- Name bn bold 1.5rem, name en muted 1rem below
- Meta chips: constituency | party | MP ID — small teal pills inline

---

## ICONS

Use **Bootstrap Icons** (`bi` prefix) throughout:
```
bi-person-fill       — MP / user
bi-building          — Parliament / institution
bi-briefcase-fill    — Ministry
bi-people-fill       — Committee
bi-globe             — Foreign travel
bi-journal-text      — Reports
bi-gear-fill         — Settings / Master data
bi-search            — Search
bi-pencil-square     — Edit
bi-trash3            — Delete (danger)
bi-printer-fill      — Print
bi-file-earmark-pdf  — PDF export
bi-file-earmark-excel — Excel export
bi-toggle-on/off     — Active/Inactive toggle
bi-plus-lg           — Add new
bi-arrow-left        — Back
bi-three-dots-vertical — Row actions menu
```

---

## PRINT TEMPLATE (`base_print.html`)

No sidebar, no topbar. Just content.

```css
@media print {
  body { font-family: 'SolaimanLipi', serif; font-size: 12pt; color: #000; }
  .no-print { display: none !important; }
  .mp-card  { border: 1px solid #ccc; box-shadow: none; }
  table     { width: 100%; border-collapse: collapse; }
  th, td    { border: 1px solid #999; padding: 6px 8px; }
  thead     { background: #e5e7eb; }
  h2        { text-align: center; font-size: 16pt; }
}
```

Print header: Parliament emblem (center) + institution name bn + en + report title + date.

---

## RESPONSIVE BREAKPOINTS

```
Mobile  < 768px  : Sidebar collapses to bottom nav or hamburger drawer
Tablet  768–1024 : Sidebar icon-only (64px)
Desktop > 1024px : Full sidebar (240px)
```

---

## DESIGN DON'TS

- No gradients on buttons (flat color only)
- No heavy shadows (max `box-shadow: 0 1px 4px rgba(0,0,0,0.08)`)
- No rounded-pill buttons (use `border-radius: 8px` max)
- No colors other than the defined palette
- No inline styles — use utility classes or `theme.css`
- Bangla text must always use SolaimanLipi font
- Never show English-only UI — every label/button has Bangla text
