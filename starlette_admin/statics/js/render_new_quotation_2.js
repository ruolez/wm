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
    const status = full.StatusQuotation.toString().toLowerCase().replace(/\s/g, '');

    // URL для кнопок Edit/View
    const originalUrl = full._view_edit_quotation_1;
    const replacedUrl = originalUrl.replace('quotations3_tbl', 'quotations1_tbl');
    let DBname = $('#DB').text();

    // Определение состояния кнопок в зависимости от статуса
    let editButton, convertButton, printButton, deleteButton;

    // Логика для кнопок
    switch (status) {
        case 'new':
        case 'inprogress':
        case 'statuserror':
            editButton = `<a href="${replacedUrl}?DBname=${DBname}&QuotationID=${full.QuotationID}&QuotationNumber=${full.QuotationNumber}&status=view_details" onclick="setSessionStorage()">
                            <button type="button" class="btn btn-outline-success" style="font-size: 10px; width: 9%">&nbsp;Edit&nbsp;</button>
                          </a>`;
            convertButton = `<span title="Action allowed only if Quotation status is 'Locked'."><button type="button" class="btn btn-outline-warning" style="font-size: 10px;" id="ConvertButton" disabled>
                              Convert To Invoice
                             </button></span>`;
            printButton = `<button type="button" class="btn btn-outline-info" style="font-size: 10px;" id="PrintButton" onclick="SetInProgressModal({ DBname: ${null}, QuotationID: '${full.QuotationID}', QuotationNumber: '${full.QuotationNumber}' }, false, '${status}', true,${meta.row})">
                            Print
                           </button>`;
            deleteButton = `<button type="button" class="btn btn-outline-danger" style="font-size: 10px;" id="DeleteButton" onclick="DeleteQuotationT(${full.QuotationID}, event, ${meta.row})">
                             Delete
                            </button>`;
            if (status === 'statuserror') {
                printButton = `<button type="button" class="btn btn-outline-info" style="font-size: 10px;" id="PrintButton" disabled>
                                Print
                               </button>`;
            }
            break;

        case 'locked':
            editButton = `<a href="${replacedUrl}?DBname=${DBname}&QuotationID=${full.QuotationID}&QuotationNumber=${full.QuotationNumber}&status=view_details" onclick="setSessionStorage()">
                            <button type="button" class="btn btn-outline-success" style="font-size: 10px; width: 9%">&nbsp;View&nbsp;</button>
                          </a>`;
            convertButton = `<span title="Action allowed only if Quotation status is 'Locked'."><button type="button" class="btn btn-outline-warning" style="font-size: 10px;" id="ConvertButton" onclick="ShowConvertModal({ DBname: ${null}, QuotationID: '${full.QuotationID}', QuotationNumber: '${full.QuotationNumber}' }, event, false,${meta.row})">
                              Convert To Invoice
                             </button></span>`;
            printButton = `<button type="button" class="btn btn-outline-info" style="font-size: 10px;" id="PrintButton" onclick="SetInProgressModal({ DBname: ${null}, QuotationID: '${full.QuotationID}', QuotationNumber: '${full.QuotationNumber}' }, false, '${status}',true,${meta.row})">
                            Print
                           </button>`;
            deleteButton = `<button type="button" class="btn btn-outline-danger" style="font-size: 10px;" disabled>
                             Delete
                            </button>`;
            break;

        case 'converted':
            editButton = `<a href="${replacedUrl}?DBname=${DBname}&QuotationID=${full.QuotationID}&QuotationNumber=${full.QuotationNumber}&status=view_details" onclick="setSessionStorage()">
                            <button type="button" class="btn btn-outline-success" style="font-size: 10px; width: 9%">&nbsp;View&nbsp;</button>
                          </a>`;
            convertButton = `<span title="Action allowed only if Quotation status is 'Locked'."><button type="button" class="btn btn-outline-warning" style="font-size: 10px;" id="ConvertButton" disabled>
                              Convert To Invoice
                             </button></span>`;
            printButton = `<button type="button" class="btn btn-outline-info" style="font-size: 10px;" id="PrintButton" onclick="SetInProgressModal({ DBname: ${null}, QuotationID: '${full.QuotationID}', QuotationNumber: '${full.QuotationNumber}' }, false, '${status}',true,${meta.row})">
                            Print
                           </button>`;
            deleteButton = `<button type="button" class="btn btn-outline-danger" style="font-size: 10px;" id="DeleteButton" onclick="DeleteQuotationT(${full.QuotationID}, event, ${meta.row})">
                             Delete
                            </button>`;
            break;

        default:
            editButton = `<button type="button" class="btn btn-outline-secondary" style="font-size: 10px;" disabled>&nbsp;N/A&nbsp;</button>`;
            convertButton = `<button type="button" class="btn btn-outline-secondary" style="font-size: 10px;" disabled>Convert To Invoice</button>`;
            printButton = `<button type="button" class="btn btn-outline-secondary" style="font-size: 10px;" disabled>Print</button>`;
            deleteButton = `<button type="button" class="btn btn-outline-secondary" style="font-size: 10px;" disabled>Delete</button>`;
            break;
    }

    return `
        ${editButton}
        ${convertButton}
        ${printButton}
        ${deleteButton}
    `;
},

col_2: function (data, type, full, meta) {
  const isConverted = full.StatusQuotation.toString().toLowerCase() === 'converted';
  const isAdminOrManager = full.isManager || full.isAdmin;
  let currentStatus = full.StatusQuotation.toString().replace(/\s/g, '').toLowerCase();
  let qnum = full.QuotationNumber.toString();



  const dropdownItems = getDropdownItems(currentStatus, meta.row, full.QuotationID, qnum);

  // Все пользователи видят dropdown и могут изменять статус
  return `
  <div class="dropdown" style="${isConverted ? 'opacity: 0.5; pointer-events: none;' : ''}">
    <button class="btn btn-custom-light  dropdown-toggle fixed-width-button-status justify-content-between justify-content-start" type="button" id="statusQuotation-${meta.row}"
      data-bs-toggle="dropdown" aria-expanded="false" data-value="${full.StatusQuotation}" tabindex="-1">
      ${full.StatusQuotation}
    </button>
    <ul class="dropdown-menu scrollable-menu" aria-labelledby="statusQuotation-${meta.row}" id="priceLeveldownmenu" style="width: 110px;">
      ${dropdownItems}
    </ul>
  </div>`;
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

function updateStatus(element, row, quotationID, quotationNumber) {
  let button = document.getElementById(`statusQuotation-${row}`);
  let oldStatus = button.innerHTML.trim();
  let newStatus = element.innerText.trim();

  if (oldStatus !== newStatus) {
    // Блокируем кнопку пока идет запрос
    button.disabled = true;

    // Отправляем запрос на обновление статуса
    // sendStatusUpdate handles table reload on success and button re-enable
    sendStatusUpdate(button, element, row, quotationID, quotationNumber, oldStatus, newStatus);
  }
}

function sendStatusUpdate(button, element, row, quotationID, quotationNumber, oldStatus, newStatus) {
  let updateObject = {
    DBname: GetDb(),
    QuotationID: quotationID,
    QuotationNumber: quotationNumber,
    OldStatus: oldStatus,
    NewStatus: newStatus
  };

  // Возвращаем Promise
  return UpdateQuotationStatus(updateObject)
    .then(response => {
      // With server-side pagination, just reload the table to get fresh data
      // The server will return the updated status from DB_admin
      let table = $('#example').DataTable();
      table.ajax.reload(null, false); // false = don't reset pagination
      button.disabled = false;
    })
    .catch(error => {
      console.error("Error updating status:", error);
      button.innerHTML = oldStatus;
      button.setAttribute('data-value', oldStatus);
      button.disabled = false;
      throw error; // Пробрасываем ошибку дальше
    });
}

function updateRowStatus(rowIndex, newStatus) {
  let table = $('#example').DataTable();
  let data = table.row(rowIndex).data();
  data.StatusQuotation = newStatus;
  table.row(rowIndex).data(data);


  table.row(rowIndex).invalidate().draw(false);
}

function getDropdownItems(currentStatus, rowIndex, quotationID, qnum) {
  const items = [];

  switch (currentStatus) {
      case 'new':
          items.push(`<li><a class="dropdown-item" data-value="1" style="width: 100%;"
              onclick="updateStatus(this, ${rowIndex}, ${quotationID}, '${qnum}');">In Progress</a></li>`);
          break;

      case 'inprogress':
          items.push(`<li><a class="dropdown-item" data-value="3" style="width: 100%;"
              onclick="showMessage('All Products must be returned to shelves!', ${rowIndex},
              () => updateStatus(this, ${rowIndex}, ${quotationID}, '${qnum}')); ">New</a></li>`);
          items.push(`<li><a class="dropdown-item" data-value="2" style="width: 100%;"
              onclick="updateStatus(this, ${rowIndex}, ${quotationID}, '${qnum}');">Locked</a></li>`);
          break;

      case 'locked':
          items.push(`<li><a class="dropdown-item" data-value="1" style="width: 100%;"
              onclick="updateStatus(this, ${rowIndex}, ${quotationID}, '${qnum}');">In Progress</a></li>`);
          break;

      case 'statuserror':
          items.push(`<li><a class="dropdown-item" data-value="3" style="width: 100%;"
              onclick="updateStatus(this, ${rowIndex}, ${quotationID}, '${qnum}');">New</a></li>`);
          items.push(`<li><a class="dropdown-item" data-value="1" style="width: 100%;"
              onclick="updateStatus(this, ${rowIndex}, ${quotationID}, '${qnum}');">In Progress</a></li>`);
          break;
  }

  return items.join('');
}

function reinitializeDropdown(rowIndex) {

  let rowData = $('#example').DataTable().row(rowIndex).data();
  $('#example').DataTable().row(rowIndex).data().StatusQuotation='In Progress';

  const table = $('#example').DataTable();
  const rowNode = table.row(rowIndex).node(); // Получаем узел строки

  // Генерируем новые элементы dropdown на основе обновленного статуса
  const newDropdownItems = getDropdownItems(
      rowData.StatusQuotation.toLowerCase().replace(/\s/g, ''),
      rowIndex,
      rowData.QuotationID,
      rowData.QuotationNumber
  );

  // Находим dropdown в строке и обновляем его содержимое
  $(rowNode).find('.dropdown-menu').html(newDropdownItems);
;
let button = rowNode.querySelector('.btn.btn-custom-light.dropdown-toggle')
if (button) {
  // Change the button text
  button.textContent = 'In Progress';
  // Update the data-value attribute if needed
  button.setAttribute('data-value', 'In Progress');
}
}


function applyStatusFilter() {
  // With serverSide: true, trigger a server reload to refresh data
  // The filter parameters are read from cookies in the ajax function
  let table = $('#example').DataTable();
  table.ajax.reload(null, false); // false = don't reset pagination
}

