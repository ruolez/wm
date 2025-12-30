var mainitemstable;
var totalColNum;
var selectboxColNum;
var qtyColNum;
let selectedModelId = GetDb();
var MaintotalColNum;
var MaintotalCostColNum;
var totaCostColNum;
var ProfitMarginColNum;
let lastFocusedElement = null;
let isLocked = false;
let currentRequest = null;
let isReadOnly =0;
const form = document.getElementById('quotationForm');


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
    return `




<a href="${full._new_quotation_delete}?id=${full.id}">
                                        <button type="button" class="btn btn-danger"  style="font-size: 12px;">
                                            Delete
                                        </button>
                                    </a>
      `;
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

$(document).ready( function () {
  toastr.options = {
    closeButton: true,
    debug: false,
    newestOnTop: false,
    progressBar: true,
    positionClass: 'toast-top-right',
    preventDuplicates: false,
    onclick: null,
    showDuration: '200',
    hideDuration: '200',
    timeOut: '5000',
    extendedTimeOut: '1000',
    showEasing: 'swing',
    hideEasing: 'linear',
    showMethod: 'fadeIn',
    hideMethod: 'fadeOut'

  };

  SetDbDropDown();
  SetTodayDate("#qdate");
  InitStates('sstate');

  TryToSetBusiness().then(async function(termsid) {

    let terms = termsid;

    if (GetDb()) {
    await  SetAdditionalFilds();
    }

    $("#dropdownMenu").on("click", ".dropdown-item",async function () {
     await SetAdditionalFilds();
    });

    if (terms){
      FillTerms(terms);
    }

});


});



$(document).ready(function () {
  initCopyButton();
  initResetShipButton();
  initGetShippingFromCustomer();
  InitMasks();
  addDropdownListeners();
  addButtonListeners();
});

$(document).ready(function () {
  $("#example").on("click", "tbody", function () {
    // $(this).find(".btn-outline-danger").removeClass("btn-outline-danger").addClass("btn-danger");
    // $(this).find(".btn-outline-warning").removeClass("btn-outline-warning").addClass("btn-warning");
    // $(this).find(".btn-outline-info").removeClass("btn-outline-info").addClass("btn-info");
    // $(this).find(".btn-outline-success").removeClass("btn-outline-success").addClass("btn-success");
  });
});



function SetLookingDropDown() {

}

$("#addItemButton").click(function () {
  MoveToMainTable();
});

$("#quickSearchButton").on("click", function () {
  ChangeQuickSearchParametr();
});

$("#exampleModal").on("hidden.bs.modal", function () {
  CleanSearch("#modalsearch");
  CleanDatable("#browse-items-table");

  document.getElementById("exampleModal")?.classList?.remove("disable-clicks");
  document.querySelectorAll('.form-overlay')?.forEach(function(overlay) {
    overlay.remove();
  });


  $('[data-toggle="popover"]')?.each(function() {
    $(this).popover('dispose');
  });
  $(document).off("click", "#YesRemember"); // Remove "Yes" listener
  $(document).off("click", "#NoRemember"); // Remove "No" listener

});



///search
$("#bnameInput").on("input", Debounce(async function (event) {
  var inputValue = $(this).val();
  await initBusness(inputValue, $(this).attr("id"));
}, 400));

$("#acnumInput").on("input", Debounce(async function (event) {
  var inputValue = $(this).val();
  await initBusness(inputValue, $(this).attr("id"));
}, 400));

$("#bnameInput").on("click", async function (event) {
  var inputValue = $(this).val();
  this.select();
  await initBusness(inputValue, $(this).attr("id"));
});

$("#acnumInput").on("click", async function (event) {
  var inputValue = $(this).val();
  this.select();
  await initBusness(inputValue, $(this).attr("id"));
});

///prevent focus in modal





function generateData() {
  return {
    data: [],
  };
}

/////////
function escape(value) {
  let __entityMap = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
    "/": "&#x2F;",
  };
  return String(value).replace(/[&<>"'\/]/g, function (s) {
    return __entityMap[s];
  });
}

function InitMasks() {
  $("#bphone").mask('000-000-0000');
  $("#sphone").mask('000-000-0000');

  $("#bzip").mask('00000-0000');
  $("#szip").mask('00000-0000');
}
///items table
function inDataTable() {
  var table = new DataTable("#items-table", {
    dom: 'rtS',
    scrollY: true,
    paging: false,
    lengthChange: true,
    searching: false,
    info: true,
    //colReorder: true,
    searchHighlight: true,
    info: false,
    select: true,
    fixedHeader: true,

    searchBuilder: {
      delete: `<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-trash" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"></path><line x1="4" y1="7" x2="20" y2="7"></line><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line><path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12"></path><path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3"></path></svg>`,
      left: `<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-chevron-left" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"></path><polyline points="15 6 9 12 15 18"></polyline></svg>`,
      right: `<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-chevron-right" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"></path><polyline points="9 6 15 12 9 18"></polyline></svg>`,
    },

    ajax: function (data, callback, settings) {
      callback(generateData());
    },
    columns: [
      {
        data: "Qty",

        render: function (data, type, row) {
          return (
            '<input  class="form-control m-0 form-control-table unsetbackground form-control-table width100 focusable no-spin columnOne"type="number" value="' +
            data +
            '" min="0" >'
          );
        },
        className: "td-wrapper ",
      },
      { data: "Description" },

      {
        data: "UnitPrice",
        render: function (data, type, row) {
          if (row.rememberprice >= 1) {
            return (
              '<input tabindex="-1" class="form-control m-0  form-control-table no-spin focusable columnTwo" type="number" value="' +
              parseFloat(data).toFixed(2) +
              '" min="0.00" step="0.01" style="background-color: var(--tblr-highlight-bg); data-toggle="popover" data-popover-content="" data-placement="top" >'
            );
          } else {

            return (
              '<input tabindex="-1" class="form-control m-0 unsetbackground form-control-table no-spin focusable columnTwo" type="number" value="' +
              parseFloat(data).toFixed(2) +
              '" min="0.00" step="0.01" data-toggle="popover" data-popover-content="" data-placement="top">'
            );
          }
        },
        className: "td-wrapper unitPrice",
      },

      {
        data: "UnitCost",

        render: function (data, type, row) {
          return parseFloat(data).toFixed(2);
        },
        className: "text-center",
      },
      { data: "SKU" },
      { data: "UPC" },
      {
        data: "Stock",
        orderable: false,
        className: "text-center",
      },
      {
        data: "Total",
        render: function (data, type, row) {
          return parseFloat(data).toFixed(2);
        },
        className: "text-center",
      },
      {
        data: "ProfitMargin",
        render: function (data, type, row) {
          return parseFloat(data).toFixed(2)+'%';

        },
        className: "text-center",
    },
      {
        data: "Comment",
        orderable: false,
        render: function (data, type, row) {

          return (
            '<input tabindex="-1" class="form-control m-0 form-control-table unsetbackground width100 form-control-table"type="text" value="' +data+'" >'
          );;
        },
        className: "td-wrapper",
      },
      { data: "TotalCost" },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<button tabindex="-1" onclick="removerow(event)" class="btn btn-danger w-100 btn-icon btn-sm" >' +
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-trash" tabindex="-1" >' +
            '<path stroke="none" d="M0 0h24v24H0z" fill="none" />' +
            '<path d="M4 7l16 0" />' +
            '<path d="M10 11l0 6" />' +
            '<path d="M14 11l0 6" />' +
            '<path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12" />' +
            '<path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3" />' +
            '</svg>' +
            '</button>';
        }
      }

      ,
    ],
    columnDefs: [
      {
        target: 0,
        visible: true,
        width: "5%",
      },
      {
        target: 1,
        visible: true,
        width: "40%",
      },
      {
        target: 2,
        visible: true,
        width: "10%",
      },
      {
        target: 3,
        visible: true,
      },
      {
        target: 4,
        visible: false,
        searchable: false,
      },

      {
        target: 5,
        visible: false,
      },
      {
        target: 6,
        visible: true,
        width: "10%",
      },
      {
        target: 7,
        visible: true,
        width: "10%",
      },
      {
        target: 8,
        visible: true,
        width: "10%",
      },

      {
        target: 9,
        visible: true,
        width: "25%",
      },
      {
        target: 10,
        visible: false,
      },
    ],
  });
  // $("#items-table thead th").css("font-size", "10px");
  table.MakeCellsEditable({
    columns: [0, 2, 9],
    onUpdate: UpdateMainTableItems,
  });
  MaintotalColNum = GetColNumber("items-table", "total");
  MaintotalCostColNum = GetColNumber("items-table", "totalCost");
  ProfitMarginColNum = GetColNumber("items-table", "Profit Margin");
}

function BrowseItems() {
  return new Promise(function (resolve, reject) {
    CleanDatable("#browse-items-table");

    var table = new DataTable("#browse-items-table", {
      scrollY: true,
      paging: false,
      lengthChange: true,
      searching: false,
      info: false,
      colReorder: true,
      searchHighlight: true,
      select: false,
      fixedHeader: true,
      ajax: function (data, callback, settings) {
        var inputValue = $("#modalsearch").val();

        var $emptyElement = $(".dataTables_empty");
            $emptyElement.text("No data available in table");

        if (inputValue?.length > 2) {
          lastFocusedElement = null;



          callback(generateData());
          var $emptyElement = $(".dataTables_empty");
          var originalText = $emptyElement.text();
          $emptyElement.text("Loading...");
          GetBrowseItems(ReplaceSpace(inputValue))
            .then(function (response) {

              var modifiedResponse = AddAdditionalColumns(response);
              delete modifiedResponse.error;
              delete modifiedResponse.error_info;
               // Найти элемент с классом dataTables_empty и изменить его текст на "Loading..."

               var $emptyElement = $(".dataTables_empty");
               var originalText = $emptyElement.text();
               $emptyElement.text("Loading...");
               callback(generateData());

              //$("#browse-items-table").hide();
              callback(modifiedResponse);
             // $("#browse-items-table").show();

              resolve();
            })
            .catch(function (error) {
              var $emptyElement = $(".dataTables_empty");
              var originalText = $emptyElement.text();
              $emptyElement.text("Loading...");
              callback(generateData());
              //console.error("Error fetching data:", error);
              reject(error);
            });
        }
        else {
          callback(generateData())
        }

      },

      columns: [
        {
          data: "S",
          orderable: false,
          render: function (data, type, row) {
            return (
              '<input  tabindex="-1" class="form-check-input " type="checkbox" ' +
              (data ? "checked" : "") +
              ">"
            );
          },
          className: "td-wrapper",
        },

        {
          data: "Qty",
          render: function (data, type, row) {
            return (
              '<input class="form-control m-0 form-control-table width100 focusable no-spin columnOne unsetbackground"type="number" value="' +
              data +
              '" min="0" >'
            );
          },
          className: "td-wrapper qty-column p-0",
        },
        {
          data: "Description",
        },
        {
          data: "UnitPrice",
          render: function (data, type, row) {

            if (row.rememberprice >= 1) {

              return (

                '<input tabindex="-1" class="form-control m-0 form-control-table width100 no-spin focusable columnTwo " type="number" value="' +
                parseFloat(data).toFixed(2) +
                '" min="0.00" step="0.01" style="background-color: var(--tblr-highlight-bg);" data-toggle="popover" data-popover-content="" data-placement="top">'
              );
            } else {

              return (
                '<input tabindex="-1" class="form-control m-0 form-control-table width100 no-spin focusable columnTwo unsetbackground" type="number" value="' +
                parseFloat(data).toFixed(2) +
                '" min="0.00" step="0.01" data-toggle="popover" data-popover-content="" data-placement="top">'
              );
            }
          },
          className: "td-wrapper unitPrice p-0",
        },
        {
          data: "UnitCost",
          render: function (data, type, row) {
            return parseFloat(data).toFixed(2);
          },
          className: "text-center price-column",
        },
        {
          data: "SKU",
          orderable: false,
        },
        {
          data: "UPC",
          orderable: false,
        },
        {
          data: "Stock",
          className: "text-center"
        },
        {
          data: "Total",
          render: function (data, type, row) {
            return parseFloat(data).toFixed(2);
          },
          className: "text-center price-column",
        },
        {
          data: "Comment",
        },
        {
          data: "TotalCost",
          render: function (data, type, row) {
            return parseFloat(data).toFixed(2);
          }
        },
      ],
      columnDefs: [
        {
          target: 0,
          visible: true,
          width: "1%",
        },
        {
          target: 1,
          visible: true,
          width: "5%",
        },
        {
          target: 2,
          visible: true,
          //width: '5.753125rem'
        },
        {
          target: 3,
          visible: true,
          width: "9%",
        },
        {
          target: 4,
          visible: true,
          width: "9%",
        },
        {
          target: 5,
          visible: true,
          width: "10%",
        },
        {
          target: 6,
          visible: true,
          width: "10%",
        },
        {
          target: 7,
          visible: false,
          width: "5%",
        },
        {
          target: 8,
          visible: true,
          width: "10%",
          className: "total-column",
          render: function (data, type, row, meta) {
            return type === "display" && typeof data === "number"
              ? parseFloat(data).toFixed(2)
              : data;
          },
        },
        {
          target: 9,
          visible: false,
        },
        {
          target: 10,
          visible: false,
        },
      ]

      //order: [[2, "asc"]],
    });

    table.MakeCellsEditable({
      columns: [0, 1, 3],
      onUpdate: UpdateItems,
    });



    totalColNum = GetColNumber("browse-items-table", "total");
    totaCostColNum = GetColNumber("browse-items-table", "totalCost");
    selectboxColNum = GetColNumber("browse-items-table", "s");
    qtyColNum = GetColNumber("browse-items-table", "qty");

    let tbl = $(".table").find('th').attr('tabindex', -1);

    //tbl.find('th').attr('tabindex', -1);

  });
}


function findDuplicatesInQutation(arr) {
  const seen = new Set();
  const duplicates = [];

  for (const item of arr) {
    if (seen.has(item)) {
      duplicates.push(item);
    } else {
      seen.add(item);
    }
  }

  return duplicates;
}




function CheckItemInQuatation(SKU) {
  var tableData = $("#items-table").DataTable().rows().data().toArray();
  return tableData.filter(function (item) {
    return item.SKU === SKU;
  });
}

async function SetAdditionalFilds() {
  let data = await GetAdditionalInfo();

  Object.entries(data).forEach(([fieldName, fieldValue]) => {
    // Create dropdown for the current field
    if (Array.isArray(fieldValue)) {

      CreateDropdowns(fieldName + "DropDown", fieldValue);
    }
  });

  $('#items-table').DataTable().clear().draw();

  await GetQuotation();

  if (CheckDBBlock()) {

    SetDBDropDown(true);
  }
  InitSearchSection();
  if ((!$('#qnumber')?.val())) {
    ChangeSalesRep(data['currentSalesRep'], data['salesRep']);
  }
  InitMasks();



}

function initResetShipButton() {
  $("#resetShip").click(function () {
    ResetShip();
  });
}

function ResetShip() {
  $("#sstreet").val("");
  $("#shipName").val("");
  $("#sstreet2").val("");
  $("#scity").val("");
  $("#sstate").val("");
  $("#sstate").attr("data-id", "");
  $("#szip").val("");
  $("#szip").attr("data-id", "");
  $("#scname").val("");
  $("#sphone").val("");
}

function ResetBill() {
  $("#bstreet").val("");
  $("#bstreet2").val("");
  $("#bcity").val("");
  $("#bstate").val("");
  $("#bstate").attr("data-id", "");
  $("#bzip").val("");
  $("#bcname").val("");
  $("#bphone").val("");
}

function initCopyButton() {
  $("#copyButton").click(function () {
    $("#sstreet").val($("#bstreet").val());
    $("#sstreet2").val($("#bstreet2").val());
    $("#scity").val($("#bcity").val());

    $("#sstate").val($("#bstate").val());
    $("#sstate").attr("data-id", $("#bstate").attr("data-id"));

    $("#szip").val($("#bzip").val());
    $("#scname").val($("#bcname").val());
    $("#sphone").val($("#bphone").val());
  });
}

async function initGetShippingFromCustomer() {
  $("#getShipfromCustomer").click(async function () {
    let val = $("#acnumInput").val();

    if (val) {
      try {
        let account = await GetBusneessInfo(val, "acnumInput");
        if (account.data.length == 1) {
          FillShipping(account.data[0]);
        }
      } catch (error) {
        console.error(error);
      }
    }
  });
}

function ShowCustomerMemo(message) {
  $('#customerMemo')?.text(message)


}

function CreateDropdowns(dropdownId, items) {

  if (Array.isArray(items)) {
    // Clear existing dropdown items
    $(`#${dropdownId} ul.dropdown-menu`).empty();

    // Add items
    items.forEach((item) => {
      const listItem = $("<li>");
      const anchor = $("<a>", {
        class: "dropdown-item",
        "data-value": item.id,
        text: item.name,
      });
      listItem.append(anchor);
      $(`#${dropdownId} ul.dropdown-menu`).append(listItem);
    });

  }

}

async function initBusness(inputValue, name) {
  autocomplete(document.getElementById(name));
}

function autocomplete(inp) {
  /*the autocomplete function takes two arguments,
  the text field element and an array of possible autocompleted values:*/
  var currentFocus;
  /*execute a function when someone writes in the text field:*/


  inp.addEventListener("click", async function (e) {
    val = this.value;
    let jsonData = [];
    if (this.id !== 'sstate') {
      jsonData = await GetBusneessInfo(val, this.id);
    }
    else {
      jsonData = await GetStatesList();
    }

    if (jsonData.data.length > 0) {
      ProcessAutoComplite(val, inp, jsonData);
    }
  });

  inp.addEventListener("input", Debounce(async function (e) {
    val = this.value;
    let jsonData = [];
    if (this.id !== 'sstate') {
      jsonData = await GetBusneessInfo(val, this.id);
    } else {
      jsonData = await GetStatesList();
    }

    if (jsonData.data.length > 0) {
      this.setAttribute('data-id', '');
      ProcessAutoComplite(val, inp, jsonData);
    }
  }, 400));

  /*execute a function presses a key on the keyboard:*/
  inp.addEventListener("keydown", function (e) {
    var x = document.getElementById(this.id + "autocomplete-list");
    if (x) x = x.getElementsByTagName("div");
    if (e.keyCode == 40) {
      /*If the arrow DOWN key is pressed,
        increase the currentFocus variable:*/
      currentFocus++;
      /*and and make the current item more visible:*/
      addActive(x);
    } else if (e.keyCode == 38) {
      //up
      /*If the arrow UP key is pressed,
        decrease the currentFocus variable:*/
      currentFocus--;
      /*and and make the current item more visible:*/
      addActive(x);
    } else if (e.keyCode == 13) {
      /*If the ENTER key is pressed, prevent the form from being submitted,*/
      e.preventDefault();
      if (currentFocus > -1) {
        /*and simulate a click on the "active" item:*/
        if (x) x[currentFocus].click();
      }
    }
  });

  function createAutoCompleteItem(inp, val, arr, i) {
    var b = document.createElement("DIV");
    b.setAttribute("class", "dropdown-item");

    if (inp?.id == "acnumInput") {
      b.innerHTML = "<a>" +
        "<strong>" + arr.data[i].anum.substr(0, val.length) + "</strong>" + arr.data[i].anum.substr(val.length) + "</a>";
      // b.innerHTML += ;

      b.innerHTML +=
        "<input type='hidden' id='" +
        arr.data[i].id +
        "' value='" +
        arr.data[i].anum +
        "'>";
    } else if ((inp?.id == "bnameInput")) {
      b.innerHTML = "<a>" +
        "<strong>" + arr.data[i].bname.substr(0, val.length) + "</strong>" + arr.data[i].bname.substr(val.length) + "</a>";
      // b.innerHTML += "<a>" + ;

      b.innerHTML +=
        "<input type='hidden' id='" +
        arr.data[i].id +
        "' value='" +
        arr.data[i].bname +
        "'>";
    } else {
      b.innerHTML = "<a>" +
        "<strong>" + arr.data[i].name.substr(0, val.length) + "</strong>" + arr.data[i].name.substr(val.length) + "</a>";
      // b.innerHTML += "<a>" + ;

      b.innerHTML +=
        "<input type='hidden' id='" +
        arr.data[i].id +
        "' value='" +
        arr.data[i].name +
        "'>";
    }

    b.addEventListener("click", function (e) {
      inp.value = this.getElementsByTagName("input")[0].value;
      let id = this.getElementsByTagName("input")[0].id;
      if (inp?.id == "bnameInput") {
        AssignBusnessAcc(id, arr);
        FillAddresesAndMemo(id, arr);

      } else if (inp?.id == "acnumInput") {
        AssignAccNum(id, arr);
        FillAddresesAndMemo(id, arr);

      } else if (inp?.id == "sstate") {
        AssignState(id, arr);
      }


      if (inp.getAttribute('data-id')) {
        EnableSearch();
        SetDBDropDown();
      } else {
        if (inp?.id == "bnameInput") {
          $("#acnumInput").val('');
          DisableSearch();
          SetDBDropDown(false);
        }
        else if (inp?.id == "acnumInput") {
          $("#bnameInput").val('');
          DisableSearch();
          SetDBDropDown(false);
        }
      }

      CloseAllLists(e.target);
    });



    return b;
  }


  function ProcessAutoComplite(val, inp, arr) {
    var a,
      i;

    CloseAllLists();


    if (inp?.id != "sstate") {
      if (!val) {
        if (inp?.id == "acnumInput") {
          $('#bnameInput').val('');
        } else if (inp?.id == "bnameInput") {
          $('#acnumInput').val('');
        }

        SetDBDropDown(CheckDBBlock());
        ResetToDefautDropDownButton('terDropdown', 'Terms');
        ResetBill();
        ResetShip();
        return false;
      } else {



        if (inp.getAttribute('data-id')) {
          EnableSearch();
          SetDBDropDown();
        }
        else {
          if (inp?.id == "bnameInput") {
            $("#acnumInput").val('');
            DisableSearch();
            SetDBDropDown(false);
          }
          else if (inp?.id == "acnumInput") {
            $("#bnameInput").val('');
            DisableSearch();
            SetDBDropDown(false);
          }
        }
      }

    }

    if ((inp?.id == "sstate") && (!val)) {
      $("#sstate").attr("data-id", "");
    }
    currentFocus = -1;

    a = document.createElement("DIV");
    a.setAttribute("id", inp.id + "autocomplete-list");
    a.setAttribute("class", "dropdown-menu show selectopened");

    a.style.maxHeight = "240px";
    a.style.overflowY = "auto";
    a.style.width = "100%";
    inp.parentNode.appendChild(a);

    let foundMatch = false;

    for (i = 0; i < arr?.data.length; i++) {

      let shouldAddAutoCompleteItem = false;

      if (inp?.id == "sstate") {
        shouldAddAutoCompleteItem = (arr.data[i].id.toUpperCase() == val.toUpperCase() || arr.data[i].name.toUpperCase().startsWith(val.toUpperCase()));
      } else {
        shouldAddAutoCompleteItem = true;
      }

      if (shouldAddAutoCompleteItem) {
        let autoCompleteItem = createAutoCompleteItem(inp, val, arr, i);
        a.appendChild(autoCompleteItem);
        foundMatch = true;
      }


    }

    if (!foundMatch) {
      a.style.display = "none";
    }



  }

  function addActive(x) {
    /*a function to classify an item as "active":*/
    if (!x) {
      return false;
    }
    /*start by removing the "active" class on all items:*/
    removeActive(x);
    if (isNaN(currentFocus)) {
      currentFocus = 0;
    }
    if (currentFocus >= x.length) currentFocus = 0;
    if (currentFocus < 0) currentFocus = x.length - 1;
    /*add class "autocomplete-active":*/
    x[currentFocus].classList.add('active');
  }
  function removeActive(x) {
    /*a function to remove the "active" class from all autocomplete items:*/
    for (var i = 0; i < x.length; i++) {
      x[i].classList.remove("active");
    }
  }

  function CloseAllLists(elmnt) {
    /*close all autocomplete lists in the document,
    except the one passed as an argument:*/
    var x = document.getElementsByClassName("selectopened");
    for (var i = 0; i < x.length; i++) {
      if (elmnt != x[i] && elmnt != inp) {
        x[i].parentNode.removeChild(x[i]);
      }
    }
  }

  document.addEventListener("click", function (e) {
    let bnameInput = document.getElementById('bnameInput');
    let acnumInput = document.getElementById('acnumInput');

    if (e.target !== bnameInput && e.target !== acnumInput && !bnameInput.contains(e.target) && !acnumInput.contains(e.target)) {
      CloseAllLists(e.target);
    }
  });
}

function InitSearchSection() {

  let bnameInput = $('#bnameInput').val();
  let acnumInput = $('#bnameInput').val();

  if (bnameInput && acnumInput) {

    EnableSearch();
  }
  else {
    DisableSearch();
  }
}

function AssignState(id, arr) {
  var foundItem = arr.data.find(function (item) {
    return item.id == id;
  });
  $("#sstate").val(foundItem.name);
  $("#sstate").attr("data-id", foundItem.id);
}

function FillAddresesAndMemo(id, arr) {
  var foundItem = arr.data.find(function (item) {
    return item.id == id;
  });

  if (foundItem) {
    FillBilling(foundItem);
    FillShipping(foundItem);
    FillTerms(foundItem.termsid);
    ShowCustomerMemo(foundItem.Memo);
  }
}

function FillTerms(termsid) {

  let $dropdownMenu = $("#termsdropdown-menu");
  let $dropdownItem = $dropdownMenu.find("[data-value='" + termsid.toString() + "']");
  if ($dropdownItem.length > 0) {
    let text = $dropdownItem.text();
    $("#terDropdown").text(text);
    $("#terDropdown").attr("data-value", termsid.toString());
  }

}

function FillSalesRep(srepid) {
  let $dropdownMenu = $("#srepdropdown-menu");
  let $dropdownItem = $dropdownMenu.find("[data-value='" + srepid.toString() + "']");
  if ($dropdownItem.length > 0) {
    let text = $dropdownItem.text();
    $("#srepDropdownButton").text(text);
    $("#srepDropdownButton").attr("data-value", srepid.toString());
  }
}

function FillShipVia(shipviaid) {

  let $dropdownMenu = $("#shipviadropdown-menu");
  let $dropdownItem = $dropdownMenu.find("[data-value='" + shipviaid.toString() + "']");
  if ($dropdownItem.length > 0) {
    let text = $dropdownItem.text();
    $("#shipviaDropdownButton").text(text);
    $("#shipviaDropdownButton").attr("data-value", shipviaid.toString());
  }

}


function FillPriceLevel(pricelevelValue) {

  let $dropdownMenu = $("#priceLeveldownmenu");
  let $dropdownItem = $dropdownMenu.find("[data-value='" + pricelevelValue.toString().toLocaleLowerCase().replace(/\s+/g, '') + "']");

  if ($dropdownItem.length > 0) {
    let text = $dropdownItem.text();
    $("#priceLevelDropdown").text(text);
    $("#priceLevelDropdown").attr("data-value", pricelevelValue);
  }

}


function FillBilling(foundItem) {
  $("#bstreet").val(foundItem.billingAddress.street);
  $("#bstreet2").val(foundItem.billingAddress.street2);
  $("#bcity").val(foundItem.billingAddress.city);
  // $("#bstate").val(foundItem.billingAddress.state);
  SetStateFromBusiness('bstate', foundItem.shippingAddress.state);

  $("#bzip").unmask();
  let zip = foundItem.billingAddress.zip;
  $("#bzip").val(zip);
  $("#bzip").mask('00000-0000');

  $("#bcname").val(foundItem.billingAddress.contactName);
  $("#bphone").unmask();
  let phone = foundItem.billingAddress.phone;
  $("#bphone").val(phone);
  if (phone.match(/^\d{10}$/)) {
    $("#bphone").mask('000-000-0000');
  }
}

function FillShipping(foundItem) {
  $("#shipName").val(foundItem.shippingAddress.shipName);
  $("#sstreet").val(foundItem.shippingAddress.street);
  $("#sstreet2").val(foundItem.shippingAddress.street2);
  $("#scity").val(foundItem.shippingAddress.city);

  SetStateFromBusiness('sstate', foundItem.shippingAddress.state);

  $("#szip").unmask();
  let zip = foundItem.billingAddress.zip;
  $("#szip").val(zip);
  $("#szip").mask('00000-0000');


  $("#scname").val(foundItem.shippingAddress.contactName);
  $("#sphone").unmask();
  let phone = foundItem.billingAddress.phone;
  $("#sphone").val(phone);
  if (phone.match(/^\d{10}$/)) {
    $("#sphone").mask('000-000-0000');
  }

}

function SetStateFromBusiness(name, id) {
  GetStatesList().then(statesList => {
    const foundState = statesList.data.find(state => state.id === id);
    if (foundState) {
      $('#' + name).val(foundState.name);
      $('#' + name).attr('data-id', foundState.id);
    }
  });


}

function PrepareMainFields() {
  return {
    DB: GetDb(),
    qnumber: $("#qnumber").val(),
    qdate: $("#qdate").val(),
    QuotationID:$('#QuotationID').val()||0,
    accountnum: $("#acnumInput").val(),
    businessname: $("#bnameInput").val(),
    CustomerID: $("#acnumInput").attr('data-id'),

    customerMemo: $('#customerMemo')?.val() || '',

    srep: parseInt($("#srepDropdownButton").attr("data-value") || 0),

    shipto: $("#shipName").val(),
    sstreet: $("#sstreet").val(),
    sstreet2: $("#sstreet2").val(),
    scity: $("#scity").val(),

    sstate: $("#sstate").attr("data-id"),

    szip: $("#szip").val() ? $("#szip").cleanVal() : "",

    scname: $("#scname").val(),

    sphone: $("#sphone").val() ? $("#sphone").cleanVal() : "",

    shipvia: parseInt($("#shipviaDropdownButton").attr("data-value") || 0),
    terms: parseInt($("#terDropdown").attr("data-value") || 0),
    bstreet: $("#bstreet").val(),
    bstreet2: $("#bstreet2").val(),
    bcity: $("#bcity").val(),

    bstate: $("#bstate").attr("data-id"),

    bzip: $("#bzip").val() ? $("#bzip").cleanVal() : "",

    bcname: $("#bcname").val(),

    bphone: $("#bphone").val() ? $("#bphone").cleanVal() : "",
    pricelevel:$('#priceLevelDropdown').text()|| 'Custom',

    qtotal: parseFloat($("#totalprice").find("strong").eq(0).text()),
  };
}

function PrepareItemsTable() {
  var table = $("#items-table").DataTable();
  var tableData = table.rows().data().toArray();


  var editedTableData = tableData.map(item => ({ ...item }));

  editedTableData.forEach((item) => {

    delete item.Stock;
    delete item.S;
    item.Total = parseFloat(item.Total);
    item.TotalCost = parseFloat(item.TotalCost);
    item.Qty = parseInt(item.Qty)
  });

  return editedTableData;
}

function AddUnitPriceColumn(tableData) {
  tableData.forEach(function (item) {
    let unitPrice = parseFloat(item.UnitPrice);
    let totalCost = unitPrice * item.Qty;
    item.TotalCost = totalCost;
  });
  return tableData;
}

function AssignQuotationNumber(number) {
  $('#qnumber').val(number);
}

function ChangeToEditFields() {


  $('#removeButton').removeAttr('disabled');



  $('#labelH1').text('EDIT QUOTATION');

}

function ValidateForm() {
  let accountnum = $("#acnumInput");
  let businessname = $("#bnameInput");
  let srep = $("#srepDropdownButton");
  let srepValue = parseInt(srep.attr("data-value") || 0);
  let items = $('#items-table').DataTable().data();

  let errors = [];


  if (!accountnum.val()) {
    errors.push("Field 'Account Number' is not filled!");
    accountnum.addClass('invalid-input');
  } else {
    accountnum.removeClass('invalid-input');
  }
  if (!businessname.val()) {
    errors.push("Field 'Business Name' is not filled!");
    businessname.addClass('invalid-input');
  } else {
    businessname.removeClass('invalid-input');
  }
  if (srepValue === 0) {
    errors.push("Field 'Sales Rep' should be selected!");
    srep.addClass('invalid-input');
  } else {
    srep.removeClass('invalid-input');
  }
  if (items.length <= 0) {
    errors.push("At least one item should be in quotation!");
    $('#items-table').parent().addClass('invalid-input');
  } else {
    $('#items-table').parent().removeClass('invalid-input');
  }

  if (errors.length > 0) {
    //toastr.error("Validation error(s):");
    errors.forEach(function (error) {
      toastr.error(error);
    });
    return false;
  }

  return true;
}

function ShowInvoiceLabel(value) {
  let newText = "Converted\nInvoice N " + value.toString();


  $("#invoiceLabel").text(newText);
  $('#invoiceLabel').removeClass('display-none');
}

async function PopulateQuotationDetails(data) {

  $('#IsManager').val(data.isManager ||0);
  $('#IsAdmin').val(data.isAdmin||0);

  $('#ReadOnly').val(data.ReadOnly||0);
  $('#ReadOnlyUser').val(data.ReadOnlyUser||'test user');
  $('#ReadOnlyTime').val(data.ReadOnlyTime||'date');



  $('#qnumber').val(data?.qnumber);
  $('#QuotationID').val(data?.QuotationID ?? 0);
  $('#InvoiceNumber').val(data?.InvoiceNumber ?? '');
  if ($('#InvoiceNumber').val()) {
    ShowInvoiceLabel($('#InvoiceNumber').val());
  } else {
    if (data?.StatusQuotation) {
      $("#invoiceLabel").text(data?.StatusQuotation);
      $('#invoiceLabel').removeClass('display-none');
    }
    else if (data?.StatusQuotation.trim() == ""){
      $("#invoiceLabel").text('Status Error');
      $('#invoiceLabel').removeClass('display-none');
    }
  }


  let formattedDate;
  let qdate = data?.qdate;
if (qdate) {
  // Split the date string and manually reorder it
  const [month, day, year] = qdate.split('-');

  // Create a new Date object using the correct format (YYYY-MM-DD)
   formattedDate = new Date(`${year}-${month}-${day}`).toISOString().split('T')[0];


}

  $('#qdate').val(formattedDate)

  $("#bnameInput").val(data?.businessname);
  $("#bnameInput").attr("data-id", data?.CustomerID);

  $("#acnumInput").val(data?.accountnum);
  $("#acnumInput").attr("data-id", data?.CustomerID);

  FillTerms(data?.terms||1);
  FillSalesRep(data?.srep||1);
  FillShipVia(data?.shipvia||1);

  FillPriceLevel(data?.pricelevel||'Custom');
  $('#shipName').val(data?.shipto);
  $('#sstreet').val(data?.sstreet);
  $('#sstreet2').val(data?.sstreet2);
  $('#scity').val(data?.scity);
  SetStateFromBusiness('sstate', data?.sstate);
  //$('#sstate').val(data.sstate);

  $('#szip').val(data?.szip);
  $('#scname').val(data?.scname);
  $("#sphone").unmask();
  let phone = data?.sphone;
  $("#sphone").val(phone);
  if (phone.match(/^\d{10}$/)) {
    $("#sphone").mask('000-000-0000');
  }

  $('#bstreet').val(data?.bstreet);
  $('#bstreet2').val(data?.bstreet2);
  $('#bcity').val(data?.bcity);
  SetStateFromBusiness('bstate', data?.bstate);


  $('#bzip').val(data?.bzip);
  $('#bcname').val(data?.bcname);

  $('#bphone').val(data?.bphone);

  $("#bphone").unmask();
  phone = data?.sphone;
  $("#bphone").val(phone);
  if (phone.match(/^\d{10}$/)) {
    $("#bphone").mask('000-000-0000');
  }


  if (!data?.memo) {
    let busness = await GetBusneessInfo(data.accountnum, "acnumInput");
    if (busness.length = 1) {
      ShowCustomerMemo(busness.data[0].Memo);
    }
  }
  else {
    ShowCustomerMemo(data.memo)
  }
  var tableData = [];

  data.items.forEach(function (item) {


    // item.ProfitMargin =(1 - (item.UnitCost / item.UnitPrice)) * 100;
    if (item?.UnitCost != 0) {

      item.ProfitMargin = ((item.UnitPrice / item.UnitCost) - 1)* 100;
  } else {

      item.ProfitMargin = 0;
  }
    let newItem = Object.assign({}, item);
    tableData.push(newItem);

  });

  let table = $("#items-table").DataTable();

  table.rows.add(tableData).draw();

  InitMainTableQty();
  InitMainTableUnitPrice();
  InitMainTableComment();
  UpdateTotals();
  ChangeToEditFields();



  LockQuotation();



}

function ConvertQuotation() {

  let DBname = GetDb();
  let QuotationID = $('#QuotationID').val();
  let QuotationNumber = $('#qnumber').val();

  let paramsObj = {
    DBname: DBname,
    QuotationID: QuotationID,
    QuotationNumber: QuotationNumber
  };
  ShowConvertModal(paramsObj, null, true);

}

function RefreshStock(event) {
  event?.preventDefault();
  UpdateStock();
}

async function UpdateStock(update = true) {
  let items = GetItemsForUpdate();
  if (!items?.length) return;


  let uniqueItems = items.filter((item, index, self) =>
    index === self.findIndex((t) => (
      t.SKU === item.SKU && t.UPC === item.UPC
    ))
  );

  let updatedItems = await GetUpdatedStock(uniqueItems);
  if (!updatedItems?.data_updatestock?.items?.length) return;

  let table = $('#items-table').DataTable();
  let tabledata = table.data().toArray();
  let updatetabledata = [];

  updatedItems.data_updatestock.items.forEach(item => {
    if (!item?.SKU || item?.Stock === null || item?.Stock === undefined) return;

    let matchingItems = tabledata.filter(tableItem => tableItem.SKU.toString().toLowerCase() == item.SKU.toString().toLowerCase());
    if (matchingItems.length > 0) {
      matchingItems.forEach(matchingItem => {
        matchingItem.Stock = item.Stock;
        updatetabledata.push(matchingItem);
      });
    }
  });

  table.clear().rows.add(updatetabledata).draw();

  if (update) {
    InitMainTableQty();
    InitMainTableUnitPrice();
    InitMainTableComment();
  }


}

function GetItemsForUpdate() {

  let table = $("#items-table").DataTable();
  //keep in mind SKU is 4-th column
  let skuData = table.column(4).data().toArray();
  let upcData = table.column(5).data().toArray();
  let combinedData = [];
  if (skuData.length == upcData.length) {


    for (let i = 0; i < skuData.length; i++) {
      let item = {
        "SKU": skuData[i],
        "UPC": upcData[i]
      };
      combinedData.push(item);
    }


  }
  return combinedData;
}


function ChangeSalesRep(salesRepName, salesRepArray) {
  let salesRepObj = salesRepArray.find(rep => rep.name.toLowerCase() === salesRepName.toLowerCase())

  if (salesRepObj) {
    $("#srepDropdown").text(salesRepObj.name);
    $("#srepDropdown").attr("data-value", salesRepObj.id);

    $('#srepDropdownButton').text(salesRepObj.name);
    $('#srepDropdownButton').attr("data-value", salesRepObj.id);
  }
  else {
    $("#srepDropdown").text("");
    $("#srepDropdown").attr("data-value", "");

    $('#srepDropdownButton').text("Select Sales Rep");
    $('#srepDropdownButton').attr("data-value", "");
  }


}

function ResetToDefautDropDownButton(name, defaultValue) {
  let dropdown = $('#' + name);
  dropdown?.val(defaultValue);
  dropdown?.text(defaultValue);
  dropdown?.removeAttr('data-value');
}

async function InitStates(name) {

  autocomplete($('#' + name)[0]);

  //autocomplete($('#sstate'), states);

}

async function GetStatesList() {
  return {
    data: [
      { name: "Alabama, (AL)", id: "AL" },
      { name: "Alaska, (AK)", id: "AK" },
      { name: "Arizona, (AZ)", id: "AZ" },
      { name: "Arkansas, (AR)", id: "AR" },
      { name: "California, (CA)", id: "CA" },
      { name: "Colorado, (CO)", id: "CO" },
      { name: "Connecticut, (CT)", id: "CT" },
      { name: "Delaware, (DE)", id: "DE" },
      { name: "Florida, (FL)", id: "FL" },
      { name: "Georgia, (GA)", id: "GA" },
      { name: "Hawaii, (HI)", id: "HI" },
      { name: "Idaho, (ID)", id: "ID" },
      { name: "Illinois, (IL)", id: "IL" },
      { name: "Indiana, (IN)", id: "IN" },
      { name: "Iowa, (IA)", id: "IA" },
      { name: "Kansas, (KS)", id: "KS" },
      { name: "Kentucky, (KY)", id: "KY" },
      { name: "Louisiana, (LA)", id: "LA" },
      { name: "Maine, (ME)", id: "ME" },
      { name: "Maryland, (MD)", id: "MD" },
      { name: "Massachusetts, (MA)", id: "MA" },
      { name: "Michigan, (MI)", id: "MI" },
      { name: "Minnesota, (MN)", id: "MN" },
      { name: "Mississippi, (MS)", id: "MS" },
      { name: "Missouri, (MO)", id: "MO" },
      { name: "Montana, (MT)", id: "MT" },
      { name: "Nebraska, (NE)", id: "NE" },
      { name: "Nevada, (NV)", id: "NV" },
      { name: "New Hampshire, (NH)", id: "NH" },
      { name: "New Jersey, (NJ)", id: "NJ" },
      { name: "New Mexico, (NM)", id: "NM" },
      { name: "New York, (NY)", id: "NY" },
      { name: "North Carolina, (NC)", id: "NC" },
      { name: "North Dakota, (ND)", id: "ND" },
      { name: "Ohio, (OH)", id: "OH" },
      { name: "Oklahoma, (OK)", id: "OK" },
      { name: "Oregon, (OR)", id: "OR" },
      { name: "Pennsylvania, (PA)", id: "PA" },
      { name: "Rhode Island, (RI)", id: "RI" },
      { name: "South Carolina, (SC)", id: "SC" },
      { name: "South Dakota, (SD)", id: "SD" },
      { name: "Tennessee, (TN)", id: "TN" },
      { name: "Texas, (TX)", id: "TX" },
      { name: "Utah, (UT)", id: "UT" },
      { name: "Vermont, (VT)", id: "VT" },
      { name: "Virginia, (VA)", id: "VA" },
      { name: "Washington, (WA)", id: "WA" },
      { name: "West Virginia, (WV)", id: "WV" },
      { name: "Wisconsin, (WI)", id: "WI" },
      { name: "Wyoming, (WY)", id: "WY" }
    ]
  };
}


$(document).ready(function () {
  $("#quicksearch").on("keypress", function (event) {
    if (event.which === 13) {
      event.preventDefault();

      QuickSearch()
        .then(function (response) {
          AddQuickSearchItem(response);
          SetDBDropDown(CheckDBBlock());
        })
        .catch(function (error) {
          console.error(error);
        });
    }
  });

});

$(document).ready(function () {

  $('aside').one('click', '*', function (e) {
    e.preventDefault(); // Отменяем действие по умолчанию
    ;
    ShowConfirmModal(e.target.href); // Показываем модальное окно
  });
});

$(document).ready(function () {
  $(document).keydown(function (e) {
    // Check if the CTRL key and the 'P' key are pressed
    if (e.ctrlKey && (e.key === 'p' || e.keyCode === 80)) {
      e.preventDefault(); // Prevent the default print dialog

      SaveAndPrintQuotation(isLocked);

    }

    if (!isLocked){
    if (e.ctrlKey && (e.key === 's' || e.keyCode === 83)) {
      e.preventDefault(); // Prevent the default print dialog
      SaveAndCloseQuotation();
    }
  }

  });

});
$(document).ready(function () {
  $('#customerMemo').on('keydown', function (event) {
    if (event.key === 'Enter') {
      event.stopPropagation();
    }
  });
});


$(document).ready(function() {
  $('#priceLeveldownmenu .dropdown-item').on('click', async function(event) {
    let items = $('#items-table').DataTable().data().toArray().map(row => row.UPC) || [];
    let anum = $('#acnumInput').val();
    let pricelevel = $(this).data('value');

    if (items?.length > 0 && anum) {
      let response = await GetUpdatedPriceLevel(items, anum, pricelevel);

      if (UpdatePriceLevel(response)) {
        toastr.success('Items price levels have been updated.');

        // Применяем UpdateMainTableItems к каждой строке после обновления уровня цен
        let table = $('#items-table').DataTable();
        let rows = table.rows();  // Получаем все строки

        rows.every(function(rowIdx, tableLoop, rowLoop) {
          let row = this;
          let oldValue = row.data().UnitPrice; // Или другой параметр, если старое значение нужно

          // Применяем функцию обновления к каждой строке
          UpdateMainTableItems(null, row, oldValue);
        });
      } else {
        toastr.error('An error occurred when updating the price level');
      }
    }

    await UpdateStock();
    UpdateTotals();
  });
});

function UpdatePriceLevel(response) {
  let updated = false;

  var priceLookup = {};
  response.Items?.forEach(function(item) {
    var upc = Object.keys(item)[0];
    priceLookup[upc] = item[upc];
  });

  var table = $('#items-table').DataTable();
  var data = table.rows().data().toArray();

  data.forEach(function(row, index) {
    var upc = row.UPC;
    if (priceLookup[upc] !== undefined) {
      row.UnitPrice = priceLookup[upc];
      row.rememberprice = 0;
      table.row(index).data(row).draw(false);
      updated = true;

      let rowNode = table.row(index).node();


      let $rowNode = $(rowNode);


      let unitPriceCell = $rowNode.find('td.unitPrice input');


      if (unitPriceCell.length > 0) {
        unitPriceCell[0].style.backgroundColor = '';
        unitPriceCell.addClass('unsetbackground');
      }
    }
  });

  table.draw();
  return updated;
}

function initBrowseTable(inputValue) {
  if (inputValue.length >= 2) {
    BrowseItems()
      .then(function () {
        InitCheckboxes();
      }).then(function () {
        initDecription();
      })
      .then(function () {
        UpdateTableValues();
      })
      .then(function () {
        InitQty();
      })
      .then(function () {
        InitUnitPrice();
      })
      .catch(function (error) {
        console.error("Error:", error);
      });
  }
}

async function SendToProgress() {
  const saved = await SaveQuotation();
  if (saved) {
    ;
    let paramsObj = {
      DB: GetDb(),
      QuotationNumber: $('#qnumber').val()
    };
    $('#ToProgressButton').attr('disabled', true);

    let setted = await SetProgress(paramsObj, null);
    if (!setted) {
      $('#ToProgressButton').attr('disabled', false)
    }
    else {
      $("#invoiceLabel").text('InProgress');

    }
  }
}


function buildPopoverContent(shortcuts) {
  return shortcuts.map(item => `<p><strong>${item.shortcut}</strong> - ${item.text}</p>`).join('');
}
// project/statics/js/shortcuts.json
$(document).ready(function () {
  const jsonPath = '/project/statics/js/shortcuts.json';

  fetch(jsonPath)
    .then(response => response.json())
    .then(data => {

      document.getElementById('form-help').setAttribute('data-bs-content', buildPopoverContent(data));
      var popoverTrigger = new bootstrap.Popover(document.getElementById('form-help'));
    })
    .catch(error => console.error('Error loading JSON:', error));


});


function LockQuotation() {
  let status = $('#invoiceLabel').text().toLowerCase();
  if (status.includes('converted')){
    status = 'converted';
  }

  // Разблокируем форму по умолчанию
  $('input, textarea, select, button')
        .not('#CloseButton')
        .not('#print')
        .not('#closePrint')
        .not('#StatusQuotation')
        .not('.btn-close')
        .not('#bstreet')   // Excluding Street
        .not('#bstreet2')  // Excluding second Street input
        .not('#bcity')     // Excluding City
        .not('#bstate')    // Excluding State
        .not('#bzip')      // Excluding Zip
        .not('#bcname')    // Excluding Contact Name
        .not('#bphone')    // Excluding Phone
        .not('#readonlyCheck')
        .not('#dropdownMenuButton')
        .prop('disabled', false);
  // Проверяем скрытый элемент ReadOnly
  let readOnly = $('#ReadOnly').val();

  if (readOnly === '1') {
    // Блокируем элементы как для статусов locked или converted
    $('input, textarea, select, button')
      .not('#CloseButton')
      .not('#print')
      .not('#closePrint')
      .not('#StatusQuotation')
      .not('.btn-close')
      .not('#readonlyCheck')
      .prop('disabled', true);

    $('#mainqtn').css('opacity', 0.7);
    $('#printButton').hide();
    $('#print').show();
    isLocked = true;
    //$('#invoiceLabel').text('Read only');


    let readOnlyUser = $('#ReadOnlyUser').val();
    let readOnlyTime = $('#ReadOnlyTime').val();

    // Set popover content with strong tags for User and Date
    let popoverContent = `<strong>User:</strong> ${readOnlyUser}<br><strong>Date:</strong> ${readOnlyTime}`;

    // Update popover content dynamically
    $('#readonly-help').attr('data-bs-content', popoverContent);
    var popoverTrigger1 = new bootstrap.Popover(document.getElementById('readonly-help'));

    $('#readonlyContainer').show();


    return;
  }

  // Логика для кнопки "Convert to Invoice"
  $('#ConvertButton').prop('disabled', true);

  // Логика для статусов "Locked" и "Converted"
  if (status === 'locked' || status === 'converted') {
    // Заблокировать редактирование всех элементов формы
    $('input, textarea, select, button')
      .not('#CloseButton')
      .not('#print')
      .not('#closePrint')
      .not('#StatusQuotation')
      .not('.btn-close')
      .prop('disabled', true);
    document.getElementById("mainqtn").style.opacity = 0.7;
    $('#printButton').hide();
    $('#print').show();
    $('#ConvertButton').prop('disabled', false);
    if (status === 'converted') {
      $('#ConvertButton').prop('disabled', true);
      $('#removeButton').prop('disabled', false);
    }
    isLocked = true;
  }

  // Логика для статусов "new" или "inprogress"
  if (status === 'new' || status === 'inprogress') {
    $('#printButton').show();
    $('#print').hide();
  }

  // Логика для статуса "status error"
  if (status === 'status error') {
    $('#printButton').prop('disabled', true);
    $('#print').prop('disabled', true);
  }
}


function TryToSetBusiness() {
  let anum = GetBusinessFromSession();
  if (anum) {
    return GetBusneessInfo(anum, 'acnumInput').then(function(business) {

      if (business?.data[0]) {
        AssignAccNum(business?.data[0].id, business);
        AssignBusnessAcc(business?.data[0].id, business);
        FillAddresesAndMemo(business?.data[0].id, business);
        //FillTerms(business?.data[0]?.termsid);
        sessionStorage.removeItem('anum');
        return business?.data[0]?.termsid;
      }
      return null;
    });
  } else {
    return Promise.resolve(null); // Если anum нет, возвращаем null
  }
}

function GetBusinessFromSession(){
 return sessionStorage.getItem('anum');
}

function ShowConfirmModal(href=null){

  if (!IsChanged()){
    //////
    CloseQuatation(href);
  }else{
    let status = $('#invoiceLabel').text().toLowerCase();
    if (status.includes('converted')){
      status = 'converted';
    }
    let readonly = $('#ReadOnly').val().toLowerCase();

    if (status === 'locked' ||status === 'converted'|| readonly==1) {
      ProcessUnlock();
      CloseQuatation(href);
    }else{
      $('#confirmClose').modal('show');

      $('#noConfirmCloseButton').off('click').on('click', function(e) {
        ProcessUnlock();
        CloseQuatation(href);
    });

    $('#yesConfirmCloseButton').off('click').on('click', function() {
        SaveAndCloseQuotation(href);
    });
    }
  }


}


$(document).ready(function () {
  // Initialize the popover
  //$('#readonly-help').popover();

  // Prevent popover click from triggering the checkbox change
  $('#readonly-help').on('click', function (e) {
    e.stopPropagation();  // Prevent the event from bubbling up to the checkbox
  });

  // Attach a toggle event listener to the checkbox
  $('#readonlyCheck').on('change', function () {
    if (!$(this).is(':checked')) {
      // Checkbox is unchecked (read-only disabled)
      ProcessUnlock(this);
    } else {
      // Checkbox is checked (read-only enabled)
      console.log("Unlock process skipped as checkbox is checked.");
    }
  });
});


function ProcessUnlock(object=null){

let qid = $('#QuotationID').val();
if (qid){
  let obj = {
    DB: selectedModelId,
    QuotationID : $('#QuotationID').val()
  }

  UnlockQuotation(obj)
  .then(response => {
      if(response?.error==0){
        toastr.info(response.error_info + ' with id '+ response.data_removeReadOnly[0]?.QuotationID)


        if (object){
          setTimeout(() => {
            window.location.reload();
        }, 600);
        }

      }
      else{
        toastr.error("Response received:", response);
        throw error

      }


  })
  .catch(error => {
      console.error("Error occurred:", error);
  });


}



 }


 $(document).ready(function() {
  // Функция для добавления * к label
  form.addEventListener('change', (event) => {
    const targetElement = event.target;
    if (targetElement.id !== 'quicksearch') {
      Changed(); // Вызываем функцию при изменении

    }
  });
});









// Отслеживание изменений всех элементов формы


// Функция для добавления обработчика к каждому dropdown
function addDropdownListeners() {
  const dropdowns = document.querySelectorAll('.dropdown-menu');

  dropdowns.forEach(menu => {
    menu.addEventListener('click', (menuEvent) => {
      const selectedItem = menuEvent.target;
      // Если кликнули на элемент dropdown, считаем, что форма изменена
      if (selectedItem.classList.contains('dropdown-item') && !selectedItem.closest('aside')) {
        Changed();

      }
    });
  });
}


//add items
//removerow(event)

//observer.observe(document.body, { childList: true, subtree: true });
function addButtonListeners() {
  const copyButton = document.getElementById('copyButton');
  const resetShip = document.getElementById('resetShip');
  const getShipfromCustomer = document.getElementById('getShipfromCustomer');

  // Проверка на существование элементов перед добавлением обработчиков
  if (copyButton) {
    copyButton.addEventListener('click', () => {
      Changed(); // Вызываем функцию при клике

    });
  }

  if (resetShip) {
    resetShip.addEventListener('click', () => {
      Changed(); // Вызываем функцию при клике

    });
  }

  if (getShipfromCustomer) {
    getShipfromCustomer.addEventListener('click', () => {
      Changed(); // Вызываем функцию при клике

    });
  }
}

