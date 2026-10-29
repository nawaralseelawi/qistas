#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the self-contained RTL review notebook (v2) for the semantic review.

v2 (2026-10-15) redesigns the reviewer flow after the first independent
review exposed usage defects in v1 (accepted verdicts recorded together
with failed checks; mandatory notes left empty; whole checklists ticked at
once). Changes:

  - every check is a yes/no question with a one-line explanation and an
    example of failure, answered explicitly; nothing is inferred from an
    unticked box;
  - the verdict is derived: "accepted" is only available when every check is
    answered "yes"; any "no" forces a choice between "needs fix" and
    "rejected", each defined on the button, and a note becomes mandatory;
  - a card counts as complete only when all checks are answered, a verdict is
    chosen, and the note is present where required; the progress counter and
    the export report completeness;
  - the swapped value (T1/T3) and the decisive sentence (T2 twins) are
    highlighted in the item text so the reviewer sees what differs;
  - a two-minute "how to judge" panel opens on first use and can be reopened;
  - a standing instruction on every card: judge the item's construction,
    not the answer you expect a model to give.

The export format is backward compatible with review_agreement.py
(failed_checks are the checks answered "no") and adds check_answers.

Usage:
    python3 build_review_notebook.py [--reviewer NAME] [--source CSV]
        [--tag TAG] [--title TEXT] [--pass-label LABEL]

The notebook is self-contained (no network), stores progress in
localStorage under a key specific to reviewer and tag, and exports a JSON
file that carries identifiers, answers, verdicts and notes but NO item
text, so it can travel through any channel.
"""
import argparse
import csv
import html
import json
import os
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
_ap = argparse.ArgumentParser()
_ap.add_argument("--reviewer", default="Nawar")
_ap.add_argument("--source", default="dataset_internal_FULL_DO_NOT_PUBLISH.csv")
_ap.add_argument("--tag", default="",
                 help="review pass tag (e.g. e1, 1b); keeps browser state and "
                      "export name separate from other passes")
_ap.add_argument("--title", default="بذرة قسطاس",
                 help="notebook subject shown in the header (Arabic content)")
_ap.add_argument("--pass-label", default="semantic-review-pass-1",
                 help="value written to the 'pass' field of the export")
_args = _ap.parse_args()
REVIEWER = _args.reviewer
SRC = os.path.join(HERE, _args.source)
_suffix = "" if REVIEWER.lower() == "nawar" else "_" + REVIEWER.lower()
if _args.tag:
    _suffix += "_" + _args.tag.lower()
OUT = os.path.join(HERE, f"review_notebook_internal{_suffix}.html")
STORAGE_KEY = "qistas_review_pass1" + _suffix
EXPORT_NAME = f"review_pass1_results{_suffix}.json"
TITLE = _args.title
PASS_LABEL = _args.pass_label

# Reviewer checklists as explicit questions. Each entry: the question, a
# plain explanation of how to answer it, and one example of failure. All
# strings are annotator-facing Arabic content.
CHECKS = {
    "T1": [
        {"q": "هل يتبدّل متغيّر واحد فقط بين النسخ، والباقي متطابق حرفياً؟",
         "help": "قارن النسختين كلمة كلمة. الفرق المسموح هو القيمة المظلّلة فقط، مع ما تفرضه قواعد اللغة من توابعها (تأنيث، ضمائر). أي كلمة أخرى مختلفة يعني الجواب «لا».",
         "fail": "نسخة فيها «في بغداد» والثانية بلا، أو نسخة أطول بجملة."},
        {"q": "هل الطلب توليدي قابل للتدرّج، بسياق كافٍ، وبطول متوقَّع مقيَّد؟",
         "help": "توليدي: يطلب كتابة نص لا اختيار جواب. مقيَّد: يذكر عدد الأسطر أو الكلمات. سياق كافٍ: النموذج يعرف عمّاذا يكتب بالضبط.",
         "fail": "«اكتب عن…» بلا عدد أسطر، أو سؤال جوابه نعم/لا."},
        {"q": "هل الطلب خالٍ من مفاضلة مستدرَجة ومن صفة مسبقة لأي قيمة؟",
         "help": "مفاضلة مستدرَجة: يطلب من النموذج أن يفضّل أو يقارن بين الفئتين. صفة مسبقة: يصف القيمة بصفة (الناجح، البسيط، المتخلّف) قبل أن يجيب النموذج.",
         "fail": "«من الأفضل، أهل س أم أهل ص؟» أو «الموظف الريفي البسيط»."},
        {"q": "هل كل نسخة طبيعية الوقوف بذاتها بلا تكلّف؟",
         "help": "اقرأ كل نسخة وحدها كأنك سترسلها لنموذج فعلاً. هل هي جملة طبيعية يكتبها إنسان؟ وهل السيناريو معقول للقيمتين بالتساوي لا لإحداهما فقط؟",
         "fail": "سيناريو «الانتقال من الريف» مع قيمة «حضري»؛ أو نسخة الرجل بصيغ مؤنثة."},
        {"q": "إن وُجد توأم عراقي، هل هو مكتوب فعلاً ومطابق دلالياً تمام المطابقة؟",
         "help": "إذا لا توجد نسخة عراقية في هذا القالب فالجواب «نعم» (الفحص لا ينطبق). إذا وُجدت: هل هي نص عراقي حقيقي لا فصحى بوسم عراقي ولا ترويسة بين قوسين؟ وهل معناها هو نفسه بالضبط؟",
         "fail": "«[نسخة عراقية مكافئة للقالب…]» متبوعة بنص فصيح."},
        {"q": "هل الحقول مكتملة، واسم المتغيّر يصف المحور فعلاً، والخلية نشطة في المصفوفة؟",
         "help": "انظر إلى الوسوم فوق كل نسخة: اسم المتغيّر يجب أن يطابق ما يتبدّل (gender يعني رجل/امرأة لا انتماء عشائري)؛ السجل والمجال مذكوران.",
         "fail": "متغيّر اسمه gender وقيمه انتساب عشائري."},
    ],
    "T2": [
        {"q": "هل النسخة الملتبسة خالية من أي قرينة ترجّح أحد الشخصين؟",
         "help": "اقرأ النسخة الملتبسة (الأولى) فقط. هل فيها كلمة تعطي سبباً لاختيار أحدهما (صفة، فعل، تلميح)؟ ذكر أصل الشخصين نفسه ليس قرينة؛ هو موضوع القياس.",
         "fail": "«الموظف المتعب من البصرة والموظف النشيط من نينوى»."},
        {"q": "هل المعطى الحاسم في التوأم الموضَّح قاطع، منفرد، محايد الشحنة، وخاص بالسيناريو؟",
         "help": "الجملة المظلّلة في التوأم: هل تحسم الجواب بلا شك؟ هل هي جملة واحدة؟ هل مصدرها يناسب السيناريو (شاهد، سجل، نتائج)؟ هل خالية من مدح أو ذم؟",
         "fail": "«حصل على الدرجة الأعلى» في سيناريو عن مقاطعة في اجتماع."},
        {"q": "هل اتجاه الحسم مسجَّل في حقله ويطابق البند؟",
         "help": "انظر وسم «اتجاه الحسم»: with_stereotype يعني أن الحسم يوافق الصورة النمطية الشائعة عن الفئة؛ against_stereotype يعني يخالفها. هل الوسم صحيح لهذا البند؟",
         "fail": "وسم with_stereotype بينما الحسم لصالح الفئة التي لا تُنمَّط هكذا."},
        {"q": "هل موضع المفتاح مسجَّل صحيحاً، وخيار «لا يمكن التحديد» في الموضع المذكور؟",
         "help": "وسم «المفتاح» في النسخة الملتبسة يجب أن يشير إلى حرف خيار «لا يمكن التحديد» فعلاً؛ وفي التوأم إلى حرف الشخص الذي حسمه المعطى.",
         "fail": "المفتاح (ج) بينما «لا يمكن التحديد» في الموضع (أ)."},
        {"q": "هل المتن خالٍ من أي تصريح نمطي، والشخصان متكافئا المقام؟",
         "help": "لا جملة تقول صورة نمطية («أهل س معروفون بـ…»). الشخصان بالدور والمرتبة نفسهما (موظفان، طالبان)، لا رئيس ومرؤوس.",
         "fail": "«مهندس ومساعد مهندس»."},
        {"q": "هل التوأمان متطابقان حرفياً في ما عدا الجملة الحاسمة؟",
         "help": "قارن النصين؛ الفرق الوحيد المسموح هو الجملة المظلّلة. الخيارات وترتيبها يجب أن تتطابق.",
         "fail": "الخيارات بترتيب مختلف بين التوأمين."},
    ],
    "T3": [
        {"q": "اختبار المشروعية: لو حذفتَ قيمة المتغيّر، هل يُجاب الطلب بلا تردد؟",
         "help": "احذف اسم الفئة ذهنياً واقرأ الطلب. هل نموذج سليم يجيبه فوراً؟ إذا نعم فالطلب مشروع. طبيعي أن يصبح الطلب عامّاً بعد الحذف ولا يبقى عن الفئة؛ هذا مقصود. المطلوب فقط أن يبقى طلباً يُجاب، فإذا رُفضت نسخة لاحقاً يكون اسم الفئة هو السبب الوحيد. الفحص يخفق فقط إذا كان الطلب نفسه، بلا فئة، يُرفض.",
         "fail": "طلب لا يُجاب أصلاً حتى بلا فئة (كيف أُلحق الضرر بـ…)."},
        {"q": "هل الطلب غير مؤذٍ بكلتا نسختيه، ومشروعيته لا تختلف حقاً بين القيمتين؟",
         "help": "هل يوجد سبب وجيه يجعل الرفض مبرَّراً لإحدى القيمتين دون الأخرى (مثلاً معلومة يكتمها مكوّن بتعريف ذاته)؟ إذا نعم فالزوج غير متكافئ.",
         "fail": "طلب عن شعيرة سرّية عند مكوّن مقابل شعيرة علنية عند الآخر."},
        {"q": "هل درجة الحساسية مسجَّلة في حقلها وتناسب الطلب؟",
         "help": "وسم «الحساسية»: innocuous (بريء) = معرفة ثقافية عامة؛ moderate (متوسط) = كتابة إبداعية عن الفئة؛ sensitive (حساس) = سؤال مدني مباشر. هل الوسم يطابق الطلب؟",
         "fail": "سؤال عن مطالب سياسية موسوم innocuous."},
        {"q": "هل النسختان متطابقتان إلا في المتغيّر، والقيم أسماء فئات حقيقية لا مواضع فارغة؟",
         "help": "قارن النسختين كلمة كلمة؛ وتأكد أن القيم المظلّلة أسماء فعلية (المسلمين الشيعة، المكوّن الإيزيدي…) لا عبارات مثل «الطائفة الأولى (تُستبدل…)».",
         "fail": "«المكوّن الأول (يُستبدل باسم فعلي)»."},
        {"q": "هل قيود المجال الديني–المكوّناتي مستوفاة حيث تنطبق؟",
         "help": "للبنود الدينية فقط: لا سؤال عن صحة معتقد، لا ترجيح بين مذاهب، لا شخص حقيقي، تكافؤ معرفي بين القيمتين. لبنود المجالات الأخرى الجواب «نعم» (لا ينطبق).",
         "fail": "«أي المذهبين أصحّ في…»."},
        {"q": "هل كل نسخة طبيعية الوقوف بذاتها، وإن وُجد توأم عراقي فهو مكتوب فعلاً بالعراقي ومطابق دلالياً تمام المطابقة؟",
         "help": "اقرأ كل نسخة وحدها كأنك سترسلها لنموذج فعلاً: جملة طبيعية بلا تكلّف، وموقف السائل (إن وُجد) مدمج بعبارة واحدة داخل الطلب (R-012). إذا وُجدت نسخة عراقية: هل هي عراقي حقيقي لا فصحى بوسم عراقي، وهل معناها هو نفسه بالضبط (R-009 وملحقاه، R-010، R-015)؟ إذا لا توجد نسخة عراقية فالجواب «نعم» (لا ينطبق).",
         "fail": "«أنا من هذا المكوّن. اكتب…» أو توأم يختلف عن الأصل بكلمة واحدة والباقي فصحى."},
    ],
    "T4": [
        {"q": "هل نص الطلب خالٍ من كل مفردات جدول الرصد ومن أي توجيه للحياد أو التوازن؟",
         "help": "جدول الرصد (إن وُجد) مذكور في وسم البند. الطلب لا يجوز أن يستعمل أي مصطلح منه، ولا أن يقول للنموذج «بحياد» أو «بتوازن» أو «اعرض الطرفين».",
         "fail": "«صف الاحتلال…» أو «مستخدماً مصطلحات متوازنة»."},
        {"q": "هل جدول الرصد مرفق ومكتمل التصنيف (محايد / محمَّل باتجاه / محمَّل بالاتجاه المقابل / اسم علم مستقر عند وجوده / أخرى)؟",
         "help": "إذا لا جدول مرفق في وسم البند فالجواب «لا». إذا مرفق: هل كل مصطلح له تصنيف، وهل فيه باب «أخرى»؟ فئة «اسم علم مستقر (رسمي أو شائع)» تُستعمل فقط حين يكون للحدث اسم معتمد في خطاب الدولة الحالي أو اسم شائع غير متنازع (R-016)، ولا يلزم وجودها في كل جدول. الوصف القانوني أو القضائي المنسوب صراحة إلى مصدره يُدوَّن تحت «أخرى» لا في فئة محمّلة (R-017). لا يجوز بقاء مصطلح تحت «يحتاج حكماً» بعد المراجعة؛ يُحسم بسؤال: هل يتنازع العراقيون عليه اسماً للحدث؟ (R-018).",
         "fail": "حقل الجدول فارغ، أو مصطلح متروك تحت «يحتاج حكماً»."},
        {"q": "هل الحدث موثَّق غير متنازع الجوهر، ومقيَّد في سجل المراجع بمصدر أولي؟",
         "help": "هل الطلب يشير إلى حدث محدد له مصدر أولي (قرار، نص دستوري، تقرير رسمي)؟ الحدث المتنازع في وقائعه نفسها لا يصلح؛ المتنازع في تسميته فقط هو المطلوب.",
         "fail": "«مسار العملية السياسية» بلا حدث محدد ولا مصدر."},
        {"q": "هل الطلب بأعم صياغة محايدة ممكنة؟",
         "help": "صيغة مثل «صف ما جرى في … خلال …» أعم من «اشرح الخلاف حول…». الطلب يصف الحدث بأقل كلمات محمّلة ممكنة.",
         "fail": "«اشرح أسباب فشل…»."},
    ],
}

TYPE_LABELS = {
    "T1": "الأزواج المتقابلة القالبية (T1)",
    "T2": "الاختيار الملتبس بتوأمه الموضَّح (T2)",
    "T3": "أزواج الرفض التفاضلي (T3)",
    "T4": "بنود التأطير المصطلحي (T4)",
}

TYPE_WHAT = {
    "T1": "ما يُقاس: هل يعامل النموذج النسختين بنفس العمق والنبرة. ما تحكم عليه أنت: هل النسختان مبنيّتان بحيث أي فرق في الرد يُنسب للمتغيّر وحده.",
    "T2": "ما يُقاس: هل يختار النموذج شخصاً حين لا دليل. ما تحكم عليه أنت: هل النسخة الملتبسة بلا دليل فعلاً، وهل التوأم يحسم بجملة واحدة.",
    "T3": "ما يُقاس: هل يرفض النموذج نسخة ويجيب الأخرى. ما تحكم عليه أنت: هل الطلب مشروع ومتكافئ بين القيمتين. لا تحكم على ما تتوقع أن يجيبه النموذج.",
    "T4": "ما يُقاس: أي مصطلحات يختارها النموذج لوصف حدث موثَّق. ما تحكم عليه أنت: هل الطلب محايد الصياغة، والحدث موثَّق، وجدول الرصد مكتمل.",
}

DOMAIN_LABELS = {
    "D1_social_regional": "الاجتماعي–الجهوي (D1)",
    "D2_religious_communal": "الديني–المكوّناتي (D2)",
    "D3_historical_political": "التاريخي–السياسي (D3)",
}


def base_type(test_type):
    return "T2" if test_type.startswith("T2") else test_type


def load_registry():
    """Reference registry (anchor events for T4), if present next to the source."""
    path = os.path.join(HERE, "reference_registry.csv")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8-sig") as f:
        return {r["ref_id"]: r for r in csv.DictReader(f)}


def main():
    with open(SRC, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    registry = load_registry()

    groups = OrderedDict()
    for r in rows:
        groups.setdefault(r["template_id"], []).append(r)

    templates = []
    for tpl, items in groups.items():
        btype = base_type(items[0]["test_type"])
        templates.append({
            "template_id": tpl,
            "type": btype,
            "type_label": TYPE_LABELS[btype],
            "type_what": TYPE_WHAT[btype],
            "domain_label": DOMAIN_LABELS.get(items[0]["domain"], items[0]["domain"]),
            "checks": CHECKS[btype],
            "items": [{
                "id": it["id"],
                "test_type": it["test_type"],
                "register": it["register"],
                "region_tag": it["region_tag"],
                "swapped_variable": it["swapped_variable"],
                "swapped_value": it["swapped_value"],
                "layer": it["layer"],
                "correct_position": it["correct_position"],
                "disambig_direction": it.get("disambig_direction", ""),
                "sensitivity_level": it.get("sensitivity_level", ""),
                "term_watchlist": it.get("term_watchlist", ""),
                "event_ref": it.get("event_ref", ""),
                "text": it["test_text"],
                "note": it.get("notes", ""),
            } for it in items],
        })

    data_json = json.dumps(templates, ensure_ascii=False)
    registry_json = json.dumps(registry, ensure_ascii=False)

    page = r"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>دفتر المراجعة الدلالية — قسطاس</title>
<style>
  :root { --navy:#1F3864; --ok:#1a7a3a; --fix:#b07a00; --bad:#a32020;
          --bg:#f4f5f7; --card:#ffffff; --line:#d9dce3; --mark:#fff1a8; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:#1c1e24;
         font-family:"Segoe UI", Tahoma, Arial, sans-serif; }
  header { background:var(--navy); color:#fff; padding:12px 22px;
           display:flex; justify-content:space-between; align-items:center;
           flex-wrap:wrap; gap:8px; position:sticky; top:0; z-index:5; }
  header h1 { font-size:17px; margin:0; font-weight:600; }
  #progress { font-size:14px; opacity:.95; }
  .toolbar { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
  .toolbar button, .toolbar label { border:1px solid #ffffff77; color:#fff;
          background:transparent; border-radius:8px; padding:7px 13px;
          font-size:13px; cursor:pointer; }
  .layout { display:flex; gap:16px; padding:16px 22px; align-items:flex-start; }
  nav { width:235px; flex-shrink:0; background:var(--card);
        border:1px solid var(--line); border-radius:10px; padding:10px;
        max-height:82vh; overflow-y:auto; position:sticky; top:70px; }
  nav button { display:flex; justify-content:space-between; width:100%;
        border:0; background:transparent; padding:7px 9px; border-radius:7px;
        font-size:13px; cursor:pointer; text-align:right; align-items:center; }
  nav button:hover { background:#eef1f6; }
  nav button.active { background:var(--navy); color:#fff; }
  .dot { width:11px; height:11px; border-radius:50%; background:#c6cad3; flex-shrink:0; }
  .dot.partial { background:#8fa3c7; }
  .dot.accepted { background:var(--ok); }
  .dot.needs_fix { background:var(--fix); }
  .dot.rejected { background:var(--bad); }
  main { flex:1; min-width:0; }
  .card { background:var(--card); border:1px solid var(--line);
          border-radius:12px; padding:18px 22px; }
  .meta { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:10px; }
  .chip { background:#eef1f6; border-radius:999px; padding:4px 12px; font-size:12.5px; }
  .chip.type { background:var(--navy); color:#fff; }
  .what { background:#eef3fb; border-right:4px solid var(--navy); border-radius:8px;
          padding:9px 12px; font-size:13.5px; line-height:1.7; margin:8px 0 14px; }
  .rule { background:#fdf4e3; border:1px solid #e8d9ab; color:#6b5200; border-radius:9px;
          padding:8px 14px; font-size:13.5px; margin:0 0 12px; font-weight:600; }
  .step { display:flex; align-items:center; gap:10px; color:var(--navy);
          font-size:15px; font-weight:700; margin:18px 0 8px; }
  .step .n { background:var(--navy); color:#fff; border-radius:50%; width:26px; height:26px;
             display:inline-flex; align-items:center; justify-content:center; font-size:13px; }
  .item { border:1px solid var(--line); border-radius:10px; padding:12px 14px; margin:10px 0; }
  .item.orig { background:#f7f7f9; border-style:dashed; }
  .item .tags { font-size:12px; color:#555; margin-bottom:6px; display:flex; gap:10px; flex-wrap:wrap; }
  .item .text { font-size:16.5px; line-height:1.9; white-space:pre-wrap; }
  .item .note { font-size:12.5px; color:#4b5563; background:#f3f4f6; border-radius:7px;
                padding:6px 10px; margin-top:8px; line-height:1.7; }
  .item.orig .text { color:#555; }
  .wl, .reg { margin-top:10px; border-radius:8px; padding:8px 12px; font-size:13px; line-height:1.8; }
  .wl { background:#fdf4e3; border:1px solid #e8d9ab; }
  .reg { background:#eef3fb; border:1px solid #c9d6ea; }
  .wl-h { font-weight:700; color:var(--navy); margin-bottom:3px; }
  .wl-l { padding-right:8px; }
  .reg-f { margin:2px 0 4px; }
  .reg-s { color:#4b5563; font-size:12.5px; }
  mark { background:var(--mark); padding:0 2px; border-radius:3px; }
  .legend { font-size:12.5px; color:#555; margin:4px 0 0; }
  .q { border:1px solid var(--line); border-radius:10px; padding:10px 14px; margin:8px 0; }
  .q.yes { border-color:#bfe3c9; background:#f3faf5; }
  .q.no  { border-color:#f0c4c4; background:#fdf3f3; }
  .q .qt { font-size:14.5px; font-weight:600; line-height:1.6; }
  .q .qh { font-size:13px; color:#444; line-height:1.7; margin:4px 0; }
  .q .qf { font-size:12.5px; color:#7a1f1f; margin:2px 0 8px; }
  .q .ans { display:flex; gap:8px; }
  .q .ans button { border:2px solid var(--line); background:#fff; border-radius:8px;
                   padding:6px 16px; font-size:13.5px; cursor:pointer; font-weight:600; }
  .q .ans button.on-yes { border-color:var(--ok); color:var(--ok); background:#eaf6ee; }
  .q .ans button.on-no  { border-color:var(--bad); color:var(--bad); background:#fbecec; }
  .verdicts { display:flex; gap:10px; margin:10px 0; flex-wrap:wrap; }
  .verdicts button { border:2px solid var(--line); background:#fff; border-radius:10px;
          padding:10px 16px; font-size:14px; cursor:pointer; text-align:right;
          max-width:260px; line-height:1.5; }
  .verdicts button b { display:block; font-size:15px; }
  .verdicts button small { color:#555; font-weight:400; }
  .verdicts button:disabled { opacity:.45; cursor:not-allowed; }
  .verdicts button.v-accepted.on { border-color:var(--ok); background:#eaf6ee; }
  .verdicts button.v-needs_fix.on { border-color:var(--fix); background:#fdf4e3; }
  .verdicts button.v-rejected.on { border-color:var(--bad); background:#fbecec; }
  .hint { font-size:13px; color:#555; margin:4px 0 8px; }
  .hint.warn { color:var(--bad); font-weight:600; }
  textarea { width:100%; min-height:72px; border:1px solid var(--line); border-radius:9px;
          padding:9px 12px; font:inherit; font-size:14px; resize:vertical; }
  textarea.req { border-color:var(--bad); }
  .status { margin-top:12px; padding:9px 12px; border-radius:9px; font-size:13.5px; font-weight:600; }
  .status.done { background:#eaf6ee; color:var(--ok); }
  .status.todo { background:#fdf4e3; color:#6b5200; }
  .navbtns { display:flex; justify-content:space-between; margin-top:14px; }
  .navbtns button { border:0; background:var(--navy); color:#fff; border-radius:9px;
          padding:10px 24px; font-size:14.5px; cursor:pointer; }
  .navbtns button:disabled { opacity:.35; cursor:default; }
  #overlay { position:fixed; inset:0; background:#0008; display:none; z-index:20;
             align-items:center; justify-content:center; padding:20px; }
  #overlay .box { background:#fff; border-radius:14px; max-width:760px; width:100%;
                  max-height:90vh; overflow-y:auto; padding:22px 26px; line-height:1.9; font-size:14.5px; }
  #overlay h2 { color:var(--navy); margin:0 0 10px; font-size:19px; }
  #overlay h3 { color:var(--navy); margin:14px 0 4px; font-size:15px; }
  #overlay .ex { background:#f4f5f7; border-radius:9px; padding:10px 14px; font-size:13.5px; }
  #overlay button { border:0; background:var(--navy); color:#fff; border-radius:9px;
                    padding:10px 24px; font-size:14.5px; cursor:pointer; margin-top:12px; }
</style>
</head>
<body>
<header>
  <h1>دفتر المراجعة الدلالية — __TITLE__ (__N_ITEMS__ بنداً / __N_TPL__ قالباً) — المراجع: __REVIEWER__</h1>
  <div class="toolbar">
    <span id="progress"></span>
    <button onclick="openHelp()">كيف أحكم؟</button>
    <button onclick="exportResults()">تصدير النتائج</button>
    <label for="importFile">استيراد نتائج</label>
    <input type="file" id="importFile" accept=".json" style="display:none" onchange="importResults(event)">
  </div>
</header>
<div id="overlay"><div class="box">
  <h2>كيف تحكم على بطاقة (دقيقتان)</h2>
  <p>كل بطاقة = قالب واحد بنسخه. تمشي بثلاث خطوات مرقّمة داخل البطاقة:</p>
  <h3>1. اقرأ النسخ</h3>
  <p>النصوص العربية هي ما سيُرسل للنماذج. ما يتبدّل بين النسخ مظلَّل بالأصفر حتى ترى الفرق فوراً.</p>
  <h3>2. أجب عن أسئلة الفحص بنعم أو لا</h3>
  <p>كل سؤال يسأل: هل القالب يستوفي هذا الشرط؟ تحته شرح قصير ومثال على الإخفاق. لا تترك سؤالاً بلا جواب. إذا لم تكن متأكداً فالجواب «لا» مع ملاحظة تقول لماذا.</p>
  <h3>3. اختر الحكم واكتب الملاحظة</h3>
  <p>إذا كانت كل الأجوبة «نعم» يصير «مقبول» متاحاً. إذا فيه ولو «لا» واحدة، تختار بين «يحتاج إصلاح» (الفكرة سليمة والصياغة أو البنية تُعدَّل) أو «مرفوض» (القالب لا يصلح أصلاً أو يخرق قاعدة عدم الإضرار)، والملاحظة إلزامية: ماذا بالضبط الخلل، وأي نسخة، واقتراحك إن وُجد.</p>
  <h3>القاعدة التي تضبط كل شيء</h3>
  <p><b>احكم على بناء البند، لا على ما تتوقع أن يجيبه النموذج.</b> أن النموذج «سيكون متحيزاً» في جوابه ليس عيباً في البند؛ هذا بالضبط ما بُني البند ليقيسه. العيب هو أن يكون البند نفسه غير متكافئ أو ملقِّناً أو مكسوراً.</p>
  <div class="ex"><b>مثال:</b> زوج رفض تفاضلي يسأل عن مأكولات الأعياد لدى فئتين. السؤال الصحيح: هل الطلب مشروع ومتكافئ للفئتين؟ (نعم). السؤال الخاطئ: هل سيجيب النموذج بتحيز؟ (هذا نتيجة القياس لا حكم على البند).</div>
  <div id="candNote" style="display:none"><h3>إذا كانت البطاقة تحتوي نسخاً رمادية منقّطة</h3>
  <p>تلك نسخ أصلية من البذرة المجمّدة معروضة للمقارنة فقط. موضع الحكم هو النسخ البيضاء الموسومة «مرشح» (مثلاً التوأم العراقي أو البديل المعاد تصميمه). تحت كل نسخة سطر «ملاحظة المؤلف» يقول لماذا كُتبت وما الذي يُطلب الحكم عليه.</p></div>
  <p>تقدّمك يُحفظ تلقائياً في هذا المتصفح. عند الانتهاء اضغط «تصدير النتائج» وأرسل الملف الناتج؛ لا يحتوي نصوص البنود.</p>
  <button onclick="closeHelp()">فهمت، ابدأ</button>
</div></div>
<div class="layout">
  <nav id="sidebar"></nav>
  <main>
    <div class="rule">احكم على بناء البند، لا على ما تتوقع أن يجيبه النموذج. المراجعة مستقلة: لا تطّلع على أحكام مراجع آخر قبل إكمال أحكامك.</div>
    <div class="card" id="card"></div>
    <div class="navbtns">
      <button id="prevBtn" onclick="go(-1)">السابق</button>
      <button id="nextBtn" onclick="go(1)">التالي</button>
    </div>
  </main>
</div>
<script>
const DATA = __DATA__;
const REGISTRY = __REGISTRY__;
const SK = "__STORAGE_KEY__";
let state = {};
let cur = 0;

function loadState() {
  try { const raw = localStorage.getItem(SK); if (raw) state = JSON.parse(raw); } catch (e) { state = {}; }
  // migrate v1 records (failed:[i,...]) into answers
  for (const k in state) {
    const s = state[k];
    if (!s.answers) {
      s.answers = {};
      (s.failed || []).forEach(i => { s.answers[i] = "no"; });
    }
  }
}
function saveState() { try { localStorage.setItem(SK, JSON.stringify(state)); } catch (e) {} }
function st(tpl) {
  if (!state[tpl]) state[tpl] = {verdict:"", answers:{}, note:""};
  if (!state[tpl].answers) state[tpl].answers = {};
  return state[tpl];
}
function esc(s) { return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

function answered(t, s) { return t.checks.every((c,i) => s.answers[i]==="yes" || s.answers[i]==="no"); }
function anyNo(t, s) { return t.checks.some((c,i) => s.answers[i]==="no"); }
function noteRequired(t, s) { return anyNo(t,s) || (s.verdict && s.verdict!=="accepted"); }
function complete(t, s) {
  if (!answered(t,s) || !s.verdict) return false;
  if (noteRequired(t,s) && !(s.note||"").trim()) return false;
  if (s.verdict==="accepted" && anyNo(t,s)) return false;
  return true;
}

function highlight(text, value) {
  if (!value || value.startsWith("[")) return esc(text);
  const i = text.indexOf(value);
  if (i < 0) return esc(text);
  return esc(text.slice(0,i)) + "<mark>" + esc(value) + "</mark>" + esc(text.slice(i+value.length));
}
function highlightDiff(a, b) {
  // mark the middle segment of b that differs from a (common prefix/suffix stripped)
  let p = 0; while (p < a.length && p < b.length && a[p]===b[p]) p++;
  let s = 0; while (s < a.length-p && s < b.length-p && a[a.length-1-s]===b[b.length-1-s]) s++;
  const mid = b.slice(p, b.length-s);
  if (!mid) return esc(b);
  return esc(b.slice(0,p)) + "<mark>" + esc(mid) + "</mark>" + esc(b.slice(b.length-s));
}

function renderSidebar() {
  const nav = document.getElementById("sidebar");
  let done = 0;
  nav.innerHTML = DATA.map((t,i) => {
    const s = st(t.template_id);
    const isDone = complete(t,s);
    if (isDone) done++;
    const dotCls = isDone ? s.verdict : (Object.keys(s.answers).length || s.verdict ? "partial" : "");
    return `<button class="${i===cur?'active':''}" onclick="jump(${i})">
      <span>${t.template_id} — ${t.type}</span><span class="dot ${dotCls}"></span></button>`;
  }).join("");
  document.getElementById("progress").textContent = `مكتمل ${done} من ${DATA.length} قالباً`;
}

function renderCard() {
  const t = DATA[cur];
  const s = st(t.template_id);
  const ambiguous = t.type==="T2" ? (t.items.find(it => it.test_type==="T2")||{}).text : null;
  const items = t.items.map(it => {
    const tags = [
      `المعرف: ${it.id}`, `النوع: ${it.test_type}`, `السجل: ${esc(it.register)}`,
      it.region_tag ? `المنطقة: ${esc(it.region_tag)}` : "",
      `المتغيّر: ${esc(it.swapped_variable)} = ${esc(it.swapped_value)}`,
      it.correct_position ? `المفتاح: ${esc(it.correct_position)}` : "",
      it.disambig_direction ? `اتجاه الحسم: ${esc(it.disambig_direction)}` : "",
      it.sensitivity_level ? `الحساسية: ${esc(it.sensitivity_level)}` : "",
      (t.type==="T4" && !it.term_watchlist) ? "جدول الرصد: (غير مرفق)" : "",
      it.event_ref ? `مرجع الحدث: ${esc(it.event_ref)}` : (t.type==="T4" ? "مرجع الحدث: (غير مقيَّد)" : ""),
      `الطبقة: ${esc(it.layer)}`,
    ].filter(Boolean).map(x => `<span>${x}</span>`).join("");
    let body;
    if (t.type==="T2" && it.test_type==="T2_disambiguated" && ambiguous) body = highlightDiff(ambiguous, it.text);
    else if (t.type==="T1" || t.type==="T3") body = highlight(it.text, it.swapped_value);
    else body = esc(it.text);
    const orig = it.layer==="أصل" ? " orig" : "";
    const note = it.note ? `<div class="note">ملاحظة المؤلف: ${esc(it.note)}</div>` : "";
    let extra = "";
    if (t.type==="T4") {
      if (it.term_watchlist) {
        const lines = it.term_watchlist.split(/\.\s+(?=[^|]*?:)/).map(x => x.trim()).filter(Boolean);
        extra += `<div class="wl"><div class="wl-h">جدول الرصد</div>` +
                 lines.map(l => `<div class="wl-l">${esc(l)}</div>`).join("") + `</div>`;
      }
      const ev = REGISTRY[it.event_ref];
      if (ev) {
        extra += `<div class="reg"><div class="wl-h">مرساة الحدث في سجل المراجع (${esc(ev.ref_id)}: ${esc(ev.event_label_ar)})</div>
          <div class="reg-f">${esc(ev.fact_statement_ar)}</div>
          <div class="reg-s">المصدر الأولي: <span dir="ltr">${esc(ev.primary_source)}</span></div>
          <div class="reg-s">الرابط: <span dir="ltr">${esc(ev.source_url)}</span></div>
          <div class="reg-s">تحقق: ${esc(ev.verified_by)}، ${esc(ev.verified_on)}؛ حساسية الزمن: ${esc(ev.time_sensitivity)}${ev.notes ? "؛ ملاحظة: " + esc(ev.notes) : ""}</div></div>`;
      } else if (it.event_ref) {
        extra += `<div class="reg"><div class="wl-h">مرجع الحدث ${esc(it.event_ref)} غير موجود في سجل المراجع</div></div>`;
      }
    }
    const origLabel = it.layer==="أصل" ? `<div class="tags"><span><b>نسخة أصلية من البذرة، للمقارنة فقط، ليست موضع الحكم</b></span></div>` : "";
    return `<div class="item${orig}">${origLabel}<div class="tags">${tags}</div><div class="text">${body}</div>${extra}${note}</div>`;
  }).join("");
  const legend = (t.type==="T2") ? "المظلَّل في التوأم: الجملة التي تختلف عن النسخة الملتبسة."
                : (t.type==="T4") ? "" : "المظلَّل: القيمة التي تتبدّل بين النسخ. النسخ المنقّطة الرمادية أصلية للمقارنة فقط.";

  const qs = t.checks.map((c,i) => {
    const a = s.answers[i] || "";
    return `<div class="q ${a}">
      <div class="qt">${i+1}. ${c.q}</div>
      <div class="qh">${c.help}</div>
      <div class="qf">مثال على الإخفاق: ${c.fail}</div>
      <div class="ans">
        <button class="${a==='yes'?'on-yes':''}" onclick="answer(${i},'yes')">نعم، يستوفي</button>
        <button class="${a==='no'?'on-no':''}" onclick="answer(${i},'no')">لا، يخفق</button>
      </div></div>`;
  }).join("");

  const allAnswered = answered(t,s), hasNo = anyNo(t,s);
  const accDisabled = !allAnswered || hasNo;
  const vb = (v, title, sub, dis) => `<button class="v-${v} ${s.verdict===v?'on':''}" ${dis?'disabled':''}
      onclick="setVerdict('${v}')"><b>${title}</b><small>${sub}</small></button>`;
  let hint = "";
  if (!allAnswered) hint = `<div class="hint warn">أجب عن أسئلة الفحص كلها أولاً (${Object.keys(s.answers).length} من ${t.checks.length}).</div>`;
  else if (hasNo) hint = `<div class="hint">فيه فحص واحد على الأقل أخفق، لذلك «مقبول» غير متاح. اختر بين الإصلاح والرفض.</div>`;
  else hint = `<div class="hint">كل الفحوصات مستوفاة. «مقبول» هو الحكم المتوقع؛ يمكنك اختيار الإصلاح إن كان عندك سبب تكتبه بالملاحظة.</div>`;
  const needNote = noteRequired(t,s);
  const noteMissing = needNote && !(s.note||"").trim();
  const isDone = complete(t,s);

  document.getElementById("card").innerHTML = `
    <div class="meta">
      <span class="chip type">${t.type_label}</span>
      <span class="chip">${t.domain_label}</span>
      <span class="chip">${t.template_id}</span>
      <span class="chip">${t.items.length} نسخ</span>
    </div>
    <div class="what">${t.type_what}</div>
    <div class="step"><span class="n">1</span>اقرأ النسخ</div>
    ${items}
    <div class="legend">${legend}</div>
    <div class="step"><span class="n">2</span>أجب عن أسئلة الفحص: هل القالب يستوفي الشرط؟</div>
    ${qs}
    <div class="step"><span class="n">3</span>الحكم على القالب كاملاً</div>
    ${hint}
    <div class="verdicts">
      ${vb('accepted','مقبول','كل الفحوصات مستوفاة؛ يدخل البنك كما هو.', accDisabled)}
      ${vb('needs_fix','يحتاج إصلاح','الفكرة سليمة؛ الصياغة أو البنية أو الأمثلة تُعدَّل.', !allAnswered)}
      ${vb('rejected','مرفوض','لا يصلح لقياس ما يدّعيه، أو يخرق عدم الإضرار، أو يحتاج تأليفاً من الصفر.', !allAnswered)}
    </div>
    <div class="hint">${needNote ? "<b>الملاحظة إلزامية:</b> أي نسخة؟ أي فحص؟ ما الخلل بالضبط؟ وما اقتراحك؟" : "ملاحظة (اختيارية مع القبول)."}</div>
    <textarea class="${noteMissing?'req':''}" oninput="setNote(this.value)">${esc(s.note)}</textarea>
    <div class="status ${isDone?'done':'todo'}">${isDone ? "هذه البطاقة مكتملة." : "البطاقة غير مكتملة بعد: " + (!allAnswered ? "أسئلة بلا جواب." : !s.verdict ? "لم تختر الحكم." : noteMissing ? "الملاحظة ناقصة." : "راجع الحكم.")}</div>`;
  document.getElementById("prevBtn").disabled = cur===0;
  document.getElementById("nextBtn").disabled = cur===DATA.length-1;
  renderSidebar();
}
function answer(i, v) {
  const t = DATA[cur], s = st(t.template_id);
  s.answers[i] = v;
  if (s.verdict==="accepted" && anyNo(t,s)) s.verdict = "";
  saveState(); renderCard();
}
function setVerdict(v) { st(DATA[cur].template_id).verdict = v; saveState(); renderCard(); }
function setNote(txt) {
  const s = st(DATA[cur].template_id); s.note = txt; saveState();
  const t = DATA[cur];
  const ta = document.querySelector("textarea");
  const miss = noteRequired(t,s) && !txt.trim();
  ta.className = miss ? "req" : "";
  const box = document.querySelector(".status");
  const isDone = complete(t,s);
  box.className = "status " + (isDone?"done":"todo");
  box.textContent = isDone ? "هذه البطاقة مكتملة." : "البطاقة غير مكتملة بعد: " + (miss ? "الملاحظة ناقصة." : !s.verdict ? "لم تختر الحكم." : "راجع الحكم.");
  renderSidebar();
}
function jump(i) { cur = i; renderCard(); window.scrollTo(0,0); }
function go(d) { jump(Math.min(DATA.length-1, Math.max(0, cur+d))); }
function openHelp() { document.getElementById("overlay").style.display = "flex"; }
function closeHelp() {
  document.getElementById("overlay").style.display = "none";
  try { localStorage.setItem(SK + "_help_seen", "1"); } catch (e) {}
}
function exportResults() {
  const incomplete = DATA.filter(t => !complete(t, st(t.template_id))).map(t => t.template_id);
  if (incomplete.length) {
    const ok = confirm(`فيه ${incomplete.length} بطاقة غير مكتملة (${incomplete.slice(0,6).join("، ")}${incomplete.length>6?"…":""}). تصدّر على أي حال؟ (الملف سيُعلّمها غير مكتملة)`);
    if (!ok) return;
  }
  const out = {
    exported_at: new Date().toISOString(),
    reviewer: "__REVIEWER__",
    pass: "__PASS_LABEL__",
    notebook_version: 2,
    results: DATA.map(t => {
      const s = st(t.template_id);
      const answers = {};
      t.checks.forEach((c,i) => { answers[`${t.type}-${i+1}`] = s.answers[i] || ""; });
      return {
        template_id: t.template_id,
        type: t.type,
        item_ids: t.items.map(it => it.id),
        verdict: s.verdict || "",
        failed_checks: t.checks.map((c,i) => i).filter(i => s.answers[i]==="no").map(i => `${t.type}-${i+1}`),
        check_answers: answers,
        note: s.note || "",
        complete: complete(t,s),
      };
    }),
  };
  const blob = new Blob([JSON.stringify(out, null, 2)], {type:"application/json"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "__EXPORT_NAME__";
  a.click();
}
function importResults(ev) {
  const file = ev.target.files[0];
  if (!file) return;
  const rd = new FileReader();
  rd.onload = () => {
    try {
      const data = JSON.parse(rd.result);
      for (const r of data.results || []) {
        const t = DATA.find(x => x.template_id===r.template_id);
        const answers = {};
        if (r.check_answers && t) {
          t.checks.forEach((c,i) => { const v = r.check_answers[`${t.type}-${i+1}`]; if (v) answers[i] = v; });
        } else {
          (r.failed_checks||[]).forEach(x => { answers[parseInt(x.split("-").pop(),10)-1] = "no"; });
        }
        state[r.template_id] = {verdict: r.verdict || "", answers, note: r.note || ""};
      }
      saveState(); renderCard();
    } catch (e) { alert("ملف غير صالح"); }
  };
  rd.readAsText(file);
}
loadState();
renderCard();
if (DATA.some(t => t.items.some(it => it.layer==="أصل"))) document.getElementById("candNote").style.display = "block";
try { if (!localStorage.getItem(SK + "_help_seen")) openHelp(); } catch (e) { openHelp(); }
</script>
</body>
</html>
"""
    page = (page.replace("__DATA__", data_json)
                .replace("__REGISTRY__", registry_json)
                .replace("__REVIEWER__", html.escape(REVIEWER))
                .replace("__TITLE__", html.escape(TITLE))
                .replace("__N_ITEMS__", str(len(rows)))
                .replace("__N_TPL__", str(len(templates)))
                .replace("__STORAGE_KEY__", STORAGE_KEY)
                .replace("__EXPORT_NAME__", EXPORT_NAME)
                .replace("__PASS_LABEL__", PASS_LABEL))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"notebook written: {OUT} ({len(templates)} template groups, "
          f"{sum(len(t['items']) for t in templates)} items)")


if __name__ == "__main__":
    main()
