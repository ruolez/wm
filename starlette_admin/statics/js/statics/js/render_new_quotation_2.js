function escape(value) {
  let __entityMap = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
    "/": "&#x2F;",
  };
  return String(value).replace(/[&<>"'\/]/g,
    function (s) {
      return __entityMap[s];
    });
}
function null_column() {
  return '<span class="text-center text-muted">-null-</span>';
}
function empty_column() {
  return '<span class="text-center text-muted">-empty-</span>';
}
const render = {
  col_0: function (data, type, full, meta) {
    return '<input class="form-check-input dt-checkboxes" type="checkbox">';
  },
  col_1: function (data, type, full, meta) {

    if (full._check_invoice) {   
    // TODO: temp replace to better way

      const originalUrl = full._view_edit_quotation_1;
      const replacedUrl = originalUrl.replace('quotations3_tbl', 'quotations1_tbl');
      return `
<a href="${replacedUrl}?DBname=${full.DBname}&QuotationID=${full.QuotationID}&QuotationNumber=${full.QuotationNumber}&status=view_details">
                                        <button type="button" class="btn btn-success"  style="font-size: 10px;">
                                            Edit
                                        </button>
                                    </a>

                                    <button type="button" class="btn btn-primary" style="font-size: 10px;" id="PrintButton" onclick="PrintQuotation({ DBname: ${null}, QuotationID: '${full.QuotationID}', QuotationNumber: '${full.QuotationNumber}' })">
                                        Print
                                    </button>

                                    <button type="button" class="btn btn-danger"  style="font-size: 10px; id="DeleteButton" onclick="DeleteQuotationT(${full.QuotationID},event )">
                                        Delete
                                    </button>
                                    </a>

      `;


    } else {
      
  
      const originalUrl = full._view_edit_quotation_1;
      const replacedUrl = originalUrl.replace('quotations3_tbl', 'quotations1_tbl');
      return `
<a href="${replacedUrl}?DBname=${full.DBname}&QuotationID=${full.QuotationID}&QuotationNumber=${full.QuotationNumber}&state=editquotation">
                                        <button type="button" class="btn btn-success"  style="font-size: 10px;">
                                            Edit
                                        </button>
                                    </a>
 
                                    <button type="button" class="btn btn-warning" style="font-size: 10px;" id="ConvertButton" onclick="ShowConvertModal({ DBname: ${null}, QuotationID: '${full.QuotationID}', QuotationNumber: '${full.QuotationNumber}' },event)">
                                       Convert To Invoice
                                    </button>

                                    <button type="button" class="btn btn-primary" style="font-size: 10px;" id="PrintButton" onclick="PrintQuotation({ DBname: ${null}, QuotationID: '${full.QuotationID}', QuotationNumber: '${full.QuotationNumber}' })">
                                       Print
                                    </button>
                                


                                <button type="button" class="btn btn-danger"  style="font-size: 10px; id="DeleteButton" onclick="DeleteQuotationT( ${full.QuotationID},event )">
                                Delete
                            </button>

      `;

    }


  },

  text: function render(data, type, full, meta, fieldOptions) {
    if (data == null) return null_column();
    if (Array.isArray(data) && data.length == 0) return empty_column();
    data = Array.isArray(data) ? data : [data].map((d) => escape(d)).join(",");
    if (type != "display") return data;
    return `<span class="align-middle d-inline-block text-truncate" data-toggle="tooltip" data-placement="bottom" title='${data}' style="max-width: 30em;">${data}</span>`;
  },
  boolean: function render(data, type, full, meta, fieldOptions) {
    if (data == null) return null_column();
    if (Array.isArray(data) && data.length == 0) return empty_column();
    data = Array.isArray(data) ? data : [data].map((d) => d === true);
    if (type != "display") return data.join(",");
    return `<div class="d-flex">${data
      .map((d) =>
        d === true
          ? `<div class="p-1"><span class="text-center text-success"><i class="fa-solid fa-check-circle fa-lg"></i></span></div>`
          : `<div class="p-1"><span class="text-center text-danger"><i class="fa-solid fa-times-circle fa-lg"></i></span></div>`
      )
      .join("")}</div>`;
  },
  email: function render(data, type, full, meta, fieldOptions) {
    if (data == null) return null_column();
    if (Array.isArray(data) && data.length == 0) return empty_column();
    data = Array.isArray(data) ? data : [data].map((d) => escape(d));
    if (type != "display") return data.join(",");
    return `<span class="align-middle d-inline-block text-truncate" data-toggle="tooltip" data-placement="bottom" title='${data}' style="max-width: 30em;">${data.map(
      (d) => '<a href="mailto:' + d + '">' + d + "</a>"
    )}</span>`;
  },
  url: function render(data, type, full, meta, fieldOptions) {
    if (data == null) return null_column();
    if (Array.isArray(data) && data.length == 0) return empty_column();
    data = Array.isArray(data) ? data : [data].map((d) => new URL(d));
    if (type != "display") return data.join(",");
    return `<span class="align-middle d-inline-block text-truncate" data-toggle="tooltip" data-placement="bottom" title='${data}' style="max-width: 30em;">${data.map(
      (d) => '<a href="' + d + '">' + d + "</a>"
    )}</span>`;
  },
  json: function render(data, type, full, meta, fieldOptions) {
    if (type != "display") return escape(JSON.stringify(data));
    if (data) {
      return `<span class="align-middle d-inline-block text-truncate" data-toggle="tooltip" data-placement="bottom" title='${escape(
        JSON.stringify(data)
      )}' style="max-width: 30em;">${pretty_print_json(data)}</span>`;
    } else return null_column();
  },
  image: function render(data, type, full, meta, fieldOptions) {
    if (!data) return null_column();
    if (Array.isArray(data) && data.length == 0) return empty_column();
    let urls = (Array.isArray(data) ? data : [data]).map((d) => new URL(d.url));
    if (type != "display") return urls;
    return `<div class="d-flex">${urls
      .map(
        (url) =>
          `<div class="p-1"><span class="avatar avatar-sm" style="background-image: url(${url})"></span></div>`
      )
      .join("")}</div>`;
  },
  file: function render(data, type, full, meta, fieldOptions) {
    if (!data) return null_column();
    if (Array.isArray(data) && data.length == 0) return empty_column();
    data = Array.isArray(data) ? data : [data];
    if (type != "display") return data.map((d) => new URL(d.url));
    return `<div class="d-flex flex-column">${data
      .map(
        (e) =>
          `<a href="${new URL(e.url)}" class="btn-link">
          <i class="fa-solid fa-fw ${get_file_icon(
            e.content_type
          )}"></i><span class="align-middle d-inline-block text-truncate" data-toggle="tooltip" data-placement="bottom" title="${escape(
            escape(e.filename)
          )}" style="max-width: 30em;">${escape(e.filename)}</span></a>`
      )
      .join("")}</div>`;
  },
  relation: function render(data, type, full, meta, fieldOptions) {
    if (!data) return null_column();
    if (Array.isArray(data) && data.length == 0) return empty_column();
    data = Array.isArray(data) ? data : [data];
    if (type != "display") return data.map((d) => d._repr).join(",");
    return `<div class="d-flex flex-row">${data
      .map(
        (e) =>
          `<a class='mx-1 btn-link' href="${e._detail_url}"><span class='m-1 py-1 px-2 badge bg-blue-lt lead d-inline-block text-truncate' data-toggle="tooltip" data-placement="bottom" title='${e._repr}'  style="max-width: 20em;">${e._repr}</span></a>`
      )
      .join("")}</div>`;
  },
};


