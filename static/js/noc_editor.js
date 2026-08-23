/* Shared CKEditor 5 initialiser for the NOC document editor and the NOC
   template editor.

   Vendored super-build (static/vendor/ckeditor5/ckeditor.js), which exposes the
   UMD global `CKEDITOR`. v41 needs no licence key; the premium plugins it also
   bundles DO, so they are removed below or the editor refuses to start.

   Usage:  window.initNocEditor('#noc-editor', '#noc-form', 'bn');
*/
(function () {
  'use strict';

  // Premium/commercial plugins bundled in the super-build. Left in, each one
  // throws a licence error and the editor never mounts.
  var PREMIUM = [
    'CKBox', 'CKFinder', 'EasyImage', 'CloudServices', 'ExportPdf', 'ExportWord',
    'Comments', 'TrackChanges', 'TrackChangesData', 'RevisionHistory',
    'RealTimeCollaborativeComments', 'RealTimeCollaborativeTrackChanges',
    'RealTimeCollaborativeRevisionHistory', 'PresenceList', 'Pagination',
    'WProofreader', 'MathType', 'SlashCommand', 'Template', 'DocumentOutline',
    'FormatPainter', 'TableOfContents', 'PasteFromOfficeEnhanced', 'CaseChange',
    'AIAssistant', 'MultiLevelList', 'Uploadcare', 'PictureEditing',
    'CKBoxImageEdit', 'MergeFields', 'Mermaid'
  ];

  var TOOLBAR = [
    'undo', 'redo', '|',
    'heading', 'fontSize', '|',
    'bold', 'italic', 'underline', 'strikethrough', 'subscript', 'superscript', '|',
    'fontColor', 'alignment', '|',
    'numberedList', 'bulletedList', 'outdent', 'indent', '|',
    'link', 'insertTable', 'horizontalLine', '|',
    'removeFormat', 'sourceEditing'
  ];

  function uiLanguage() {
    var html = document.documentElement.getAttribute('lang') || '';
    return html.indexOf('bn') === 0 ? 'bn' : 'en';
  }

  window.initNocEditor = function (textareaSelector, formSelector, contentLanguage) {
    var el = document.querySelector(textareaSelector);
    if (!el) return;

    if (typeof CKEDITOR === 'undefined' || !CKEDITOR.ClassicEditor) {
      console.error('[NOC] CKEditor bundle did not load — falling back to a plain textarea.');
      el.classList.add('form-control');
      return;
    }

    CKEDITOR.ClassicEditor.create(el, {
      removePlugins: PREMIUM,
      toolbar: { items: TOOLBAR, shouldNotGroupWhenFull: true },
      // WITHOUT this, CKEditor strips the inline column widths, text-indent and
      // font sizes the NOC layout depends on, and the letterhead collapses into
      // a single column. It also keeps {placeholder} tokens untouched.
      htmlSupport: {
        allow: [{ name: /.*/, attributes: true, classes: true, styles: true }]
      },
      table: {
        contentToolbar: ['tableColumn', 'tableRow', 'mergeTableCells',
                         'tableProperties', 'tableCellProperties']
      },
      language: {
        ui: uiLanguage(),
        content: contentLanguage === 'bn' ? 'bn' : 'en'
      }
    }).then(function (editor) {
      // CKEditor writes back to the <textarea> only through its own submit
      // handling; this form posts normally, so sync it ourselves.
      var form = formSelector ? document.querySelector(formSelector) : null;
      if (form) {
        form.addEventListener('submit', function () {
          el.value = editor.getData();
        });
      }
      window.nocEditor = editor;
    }).catch(function (err) {
      console.error('[NOC] CKEditor failed to start:', err);
      el.classList.add('form-control');
      el.style.display = 'block';
    });
  };
}());
