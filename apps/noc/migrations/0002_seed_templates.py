"""Seed the default letterhead and the two document templates.

Transcribed from docs/NOC for MP/ — `NOC Sample-1/2.pdf` (English certificate)
and `NOC Bangla Sample-1/2.png` (Bangla forwarding letter). Both are scans, so
the Bangla wording should be proofread in Master Data after deploy.

Layout is **table-based on purpose**: WeasyPrint (PDF), the browser (print) and
utils/html_to_docx.py (Word) all reproduce table columns faithfully, whereas
float/flex layout survives none of the three.
"""

from django.db import migrations

LOGO = '/static/img/parliament-logo.png'

# ── English certificate ──────────────────────────────────────────────────────
EN_BODY = """
<table border="0" style="width: 100%; border-collapse: collapse">
  <tbody><tr>
    <td style="width: 18%; text-align: center; vertical-align: middle">
      <img src="''' + LOGO + '''" alt="" width="100">
    </td>
    <td style="width: 46%; text-align: center; vertical-align: middle">
      <p style="font-size: 15pt; font-weight: bold">{org_bn}</p>
      <p style="font-size: 12pt; font-weight: bold">{org_en}</p>
      <p style="font-size: 12pt">{wing_en}</p>
      <p style="font-size: 12pt">{section_en}</p>
      <p style="font-size: 11pt"><u>{website}</u></p>
    </td>
    <td style="width: 36%; text-align: right; vertical-align: middle">
      <p style="font-size: 11pt">Telephone No : {telephone}</p>
      <p style="font-size: 11pt">Fax No : {fax}</p>
      <p style="font-size: 11pt">E-mail : {email}</p>
      <p style="font-size: 11pt">{address_bn}</p>
      <p style="font-size: 11pt">{address_en}</p>
    </td>
  </tr></tbody>
</table>
<p>&nbsp;</p>
<table border="0" style="width: 100%">
  <tbody><tr>
    <td style="width: 58%">No.{memo_no}</td>
    <td style="width: 42%">Date: {issue_date_en}</td>
  </tr></tbody>
</table>
<p>&nbsp;</p>
<table border="0" style="width: 100%">
  <tbody><tr>
    <td style="width: 9%; vertical-align: top"><p style="font-weight: bold">Sub:</p></td>
    <td style="text-align: justify">
      <p style="font-weight: bold">No objection certificate for {mp_title_en} {mp_name_en},
      Hon'ble Member of Parliament to visit {countries_en}.</p>
    </td>
  </tr></tbody>
</table>
<p>&nbsp;</p>
<p style="text-align: justify; text-indent: 48px">This is to certify that {mp_title_en}
{mp_name_en}, Hon'ble Member of Parliament (Passport No-{passport_no}) has submitted an
application to visit {countries_en} from {date_range_en} or at nearest convenient
time.{spouse_clause_en} {speaker_title_en} of Bangladesh Parliament has kindly permitted the
proposed visit of {mp_title_en} {mp_name_en}, Hon'ble Member of Parliament,
{constituency_en}, constituency of Bangladesh.</p>
<p>&nbsp;</p>
<table border="0" style="width: 100%">
  <tbody><tr>
    <td style="width: 52%">&nbsp;</td>
    <td style="width: 48%; text-align: center">
      <p>&nbsp;</p>
      <p>&nbsp;</p>
      <p style="font-weight: bold">{signatory_name_en}</p>
      <p>{signatory_designation_en}</p>
      <p>Phone: {signatory_phone}</p>
      <p>Mobile: {signatory_mobile}</p>
      <p>E-mail: {signatory_email}</p>
    </td>
  </tr></tbody>
</table>
<p>&nbsp;</p>
<p style="font-weight: bold">{mp_title_en} {mp_name_en}</p>
<p>Hon'ble Member of Parliament</p>
<p>{constituency_en}</p>
<p>Bangladesh Parliament.</p>
""".replace("''' + LOGO + '''", LOGO)


# ── Bangla forwarding letter ─────────────────────────────────────────────────
# Two blocks on one page: the letter, then the অনুলিপি distribution list, each
# repeating the memo number/date and each signed.
BN_BODY = """
<p style="text-align: center; font-size: 15pt; font-weight: bold">{org_bn}</p>
<p style="text-align: center; font-size: 12pt">{wing_bn}</p>
<p style="text-align: center; font-size: 12pt">{section_bn}</p>
<p style="text-align: center; font-size: 11pt"><u>{website}</u></p>
<p>&nbsp;</p>
<table border="0" style="width: 100%">
  <tbody><tr>
    <td style="width: 62%; vertical-align: top">নং-{memo_no_bn}</td>
    <td style="width: 38%; text-align: right">
      <p>তারিখ: {bangla_date}</p>
      <p>{gregorian_date_bn}</p>
    </td>
  </tr></tbody>
</table>
<p>&nbsp;</p>
<table border="0" style="width: 100%">
  <tbody><tr>
    <td style="width: 9%; vertical-align: top">বিষয়:</td>
    <td style="text-align: justify">
      <p style="font-weight: bold">মাননীয় সংসদ-সদস্য {mp_title_bn} {mp_name_bn}-এর
      {countries_bn} সফরের অনাপত্তি সনদ (NOC) প্রদান।</p>
    </td>
  </tr></tbody>
</table>
<p style="text-align: justify; text-indent: 48px; margin-top: 10px">উপর্যুক্ত বিষয়ে জানানো যাচ্ছে যে, বাংলাদেশ
জাতীয় সংসদের মাননীয় সংসদ-সদস্য {mp_title_bn} {mp_name_bn} ব্যক্তিগত খরচে আগামী
{date_range_bn} পর্যন্ত অথবা নিকটবর্তী সুবিধাজনক সময়ে {countries_bn} সফরের অভিপ্রায় ব্যক্ত করে
মাননীয় স্পীকার বরাবর অনাপত্তি সনদ (NOC) প্রদানের জন্য আবেদন করেছেন।{spouse_clause_bn}
বাংলাদেশ জাতীয় সংসদের {speaker_title_bn} উক্ত আবেদনের পরিপ্রেক্ষিতে মাননীয় সংসদ-সদস্যের
{countries_bn} সফরের সদয় অনুমোদন প্রদান করেছেন।</p>
<table border="0" style="width: 100%; margin-top: 10px">
  <tbody><tr>
    <td style="width: 6%; vertical-align: top">২।</td>
    <td style="text-align: justify">এমতাবস্থায়, মাননীয় সংসদ-সদস্য {mp_title_bn} {mp_name_bn}
    এর {countries_bn} সফরের অনাপত্তি সনদ (NOC) জারিপূর্বক সদয় অবগতি ও প্রয়োজনীয় কার্যার্থে
    এতদসঙ্গে প্রেরণ করা হলো।</td>
  </tr></tbody>
</table>
<p style="margin-top: 10px">সংযুক্ত: অনাপত্তি সনদ।</p>
<table border="0" style="width: 100%">
  <tbody><tr>
    <td style="width: 55%">&nbsp;</td>
    <td style="width: 45%; text-align: center">
      <p>&nbsp;</p>
      <p style="font-weight: bold; margin-top: 16px">{signatory_name_bn}</p>
      <p>{signatory_designation_bn}</p>
      <p>মোবাইল: {signatory_mobile_bn}</p>
      <p>ই-মেইল: {signatory_email}</p>
    </td>
  </tr></tbody>
</table>
<p>প্রাপক:</p>
<p style="text-indent: 48px; font-weight: bold">{mp_title_bn} {mp_name_bn}</p>
<p style="text-indent: 48px">মাননীয় সংসদ-সদস্য</p>
<p style="text-indent: 48px">{constituency_bn}</p>
<p style="text-indent: 48px">বাংলাদেশ জাতীয় সংসদ</p>
<table border="0" style="width: 100%; margin-top: 12px">
  <tbody><tr>
    <td style="width: 62%; vertical-align: top">নং-{memo_no_bn}</td>
    <td style="width: 38%; text-align: right">
      <p>তারিখ: {bangla_date}</p>
      <p>{gregorian_date_bn}</p>
    </td>
  </tr></tbody>
</table>
<p>সদয় অবগতি ও প্রয়োজনীয় ব্যবস্থা গ্রহণের জন্য অনুলিপি প্রেরণ করা হলো (জ্যেষ্ঠতার ভিত্তিতে নয়) :</p>
<ol>
  <li>{speaker_title_bn}-এর একান্ত সচিব, বাংলাদেশ জাতীয় সংসদ, ঢাকা।</li>
  <li>মাননীয় চীফ হুইপের একান্ত সচিব, বাংলাদেশ জাতীয় সংসদ, ঢাকা।</li>
  <li>নির্বাহী পরিচালক, হযরত শাহজালাল আন্তর্জাতিক বিমান বন্দর, ঢাকা।</li>
  <li>সচিব এর একান্ত সচিব, বাংলাদেশ জাতীয় সংসদ সচিবালয়, ঢাকা।</li>
  <li>সিনিয়র সিস্টেম এনালিস্ট (ই-সার্ভিস ম্যানেজমেন্ট), বাংলাদেশ জাতীয় সংসদ সচিবালয়, ঢাকা।
      (অনাপত্তি সনদটি ওয়েবসাইটে প্রকাশের জন্য অনুরোধ করা হলো)</li>
  <li>যুগ্মসচিব (আইপিএএন্ডএস) এর ব্যক্তিগত কর্মকর্তা, বাংলাদেশ জাতীয় সংসদ সচিবালয়, ঢাকা।</li>
  <li>রেকর্ড।</li>
</ol>
<table border="0" style="width: 100%">
  <tbody><tr>
    <td style="width: 55%">&nbsp;</td>
    <td style="width: 45%; text-align: center">
      <p style="font-weight: bold; margin-top: 14px">{signatory_name_bn}</p>
      <p>{signatory_designation_bn}</p>
    </td>
  </tr></tbody>
</table>
"""


def seed(apps, schema_editor):
    NOCLetterhead = apps.get_model('noc', 'NOCLetterhead')
    NOCTemplate = apps.get_model('noc', 'NOCTemplate')

    if not NOCLetterhead.objects.exists():
        NOCLetterhead.objects.create()      # field defaults carry the real values

    NOCTemplate.objects.get_or_create(
        language='en', name_bn='ইংরেজি অনাপত্তি সনদ',
        defaults={'name_en': 'English No Objection Certificate',
                  'body_html': EN_BODY.strip(), 'is_default': True,
                  'is_active': True, 'ordering': 10},
    )
    NOCTemplate.objects.get_or_create(
        language='bn', name_bn='বাংলা অনাপত্তি পত্র',
        defaults={'name_en': 'Bangla NOC forwarding letter',
                  'body_html': BN_BODY.strip(), 'is_default': True,
                  'is_active': True, 'ordering': 10},
    )


def unseed(apps, schema_editor):
    apps.get_model('noc', 'NOCTemplate').objects.filter(
        name_bn__in=['ইংরেজি অনাপত্তি সনদ', 'বাংলা অনাপত্তি পত্র']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('noc', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
