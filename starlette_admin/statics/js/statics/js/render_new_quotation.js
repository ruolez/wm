var qitemstable;
var totalColNum;
var selectboxColNum;
var qtyColNum;
let selectedModelId = sessionStorage.getItem("modelDop");
var MaintotalColNum;
var MaintotalCostColNum;
var totaCostColNum;

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

$(document).ready(function () {

  toastr.options = {
    closeButton: true,
    debug: false,
    newestOnTop: false,
    progressBar: true,
    positionClass: 'toast-top-right',
    preventDuplicates: false,
    onclick: null,
    showDuration: '300',
    hideDuration: '1000',
    timeOut: '5000',
    extendedTimeOut: '1000',
    showEasing: 'swing',
    hideEasing: 'linear',
    showMethod: 'fadeIn',
    hideMethod: 'fadeOut'
};

  SetDbDropDown();
  SetTodayDate();

  if (sessionStorage.getItem('modelDop')){
    SetAdditionalFilds();
  } 


  $("#dropdownMenu").on("click", ".dropdown-item", function () {
    SetAdditionalFilds();
  });

 
 
});

////all drop down init

$(document).ready(function () {
  $(".dropdown-toggle").each(function () {
    let dropdownToggle = $(this);
    let dropdownMenu = dropdownToggle.next(".dropdown-menu");

    dropdownMenu.on("click", ".dropdown-item", function (event) {
      let selectedValue = $(this).data("value");
      let selectedText = $(this).text();

      dropdownToggle.attr("data-value", selectedValue);
      dropdownToggle.text(selectedText);
    });
  });
});

$(document).ready(function () {
  $("#lookinDropdown")
    .next(".dropdown-menu")
    .on("click", ".dropdown-item", function () {
      let inputValue = document.getElementById("modalsearch").value;
      initBrowseTable(inputValue);
    });
});

$(document).ready(function () {
  initCopyButton();
  initResetShipButton();
  initGetShippingFromCustomer();

  $("#bnameInput").on("click", function() {
 
  
  });

});


// $("#bnameInput").on("input", async function (event) {
//   var inputValue = $(this).val();
//   await initBusness(inputValue, $(this).attr("id"));
// });


///items table
function inDataTable() {
  var table = new DataTable("#items-table", {
    scrollY: true,
    paging: false,
    lengthChange: true,
    searching: false,
    info: true,
    //colReorder: true,
    searchHighlight: true,
    info: false,
    select: true,
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
            '<input  class="form-control m-0 form-control-table unsetbackground "type="number" value="' +
            data +
            '" min="0" >'
          );
        },
        className: "td-wrapper",
      },
      { data: "Description" },

      {
        data: "UnitPrice",
        render: function (data, type, row) {
          return (
            '<input class="form-control m-0 form-control-table unsetbackground"type="number" value="' +
            parseFloat(data).toFixed(2) +
            '" min="0.00"step="0.01" >'
          );
        },
        className: "td-wrapper",
      },

      { data: "UnitCost" },
      { data: "SKU" },
      { data: "UPC" },
      { data: "Stock" },
      { 
        data: "Total",
        render: function (data, type, row) {
          return parseFloat(data).toFixed(2);
        } 
      },    
      {
        data: "Comment",
        render: function (data, type, row) {
          return (
            '<input class="form-control m-0 form-control-table unsetbackground width100"type="text" value="' +
            data +
            ' >'
          );
        },
        className: "td-wrapper",
      },
      { data: "TotalCost" },
      { 
        
        render: function(data, type, row) {
          return '<button onclick="removerow(event)" class="btn btn-danger w-100 btn-icon btn-sm" >' +
                 '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-trash" >' +
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
        width: "25%",
      },
      {
        target: 3,
        visible: false,
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
        target: 9,
        visible: false,
      },
    ],
    //order: [[1, "asc"]],
  });

  // table.MakeCellsEditable({

  // });
  table.MakeCellsEditable({
    columns: [0, 2, 8],
    onUpdate: UpdateMainTableItems,
  });
  MaintotalColNum = GetColNumber("items-table", "total");
  MaintotalCostColNum = GetColNumber("items-table", "totalCost");
}

function removerow(event) {
  event.preventDefault();
  var table = $('#items-table').DataTable(); 
  var row = $(event.target).closest('tr'); 
  table.row(row).remove().draw(false); 
  UpdateTotals(); 
}


///modal when opened
$(document).on("click", "#browseItemsButton", function () {
  ///add if checked   
    CopyItemsFromQuotation(); 

});

///search
document.getElementById("modalsearch").addEventListener("input", function (event) {
    let inputValue = event.target.value;

    initBrowseTable(inputValue);
  });

 



function BrouseItems() {
  return new Promise(function (resolve, reject) {
    CleanDatable("#brouse-items-table");
   
    var table = new DataTable("#brouse-items-table", {
      scrollY: true,
      paging: false,
      lengthChange: true,
      searching: false,
      info: false,
      colReorder: true,
      searchHighlight: true,
      select: false,
      ajax: function (data, callback, settings) {
        var inputValue = $("#modalsearch").val();
        if (inputValue?.length>2){  
          GetBrowseItems(inputValue)
          .then(function (response) {
            var modifiedResponse = AddAdditionalColumns(response);
            callback(modifiedResponse);
            resolve();
          })
          .catch(function (error) {
            console.error("Error fetching data:", error);
            reject(error);
          }); 
        }
        else{
          callback(generateData())
        }    

      },
     
      columns: [
        {
          data: "S",
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
              '<input class="form-control m-0 form-control-table"type="number" value="' +
              data +
              '" min="0" >'
            );
          },
          className: "td-wrapper qty-column ",
        },
        {
          data: "Description",
        },
        {
          data: "UnitPrice",
          render: function (data, type, row) {
            return (
              '<input  tabindex="-1" class="form-control m-0 form-control-table"type="number" value="' +
              parseFloat(data).toFixed(2) +
              '" min="0.00"step="0.01" >'
            );
          },
          className: "td-wrapper",
        },
        {
            data: "UnitCost",
            render: function (data, type, row) {
              return parseFloat(data).toFixed(2);
            } 
        },
        {
          data: "SKU",
        },
        {
          data: "UPC",
        },
        {
          data: "Stock",
        },
        {
          data: "Total",
          render: function (data, type, row) {
            return parseFloat(data).toFixed(2);
          } 
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
          width: "5%",
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
          width: "5%",
        },
        {
          target: 4,
          visible: true,
          width: "5%",
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
          visible: true,
          width: "10%",
        },
        {
          target: 8,
          visible: true,
          width: "5%",
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
    

    
    totalColNum = GetColNumber("brouse-items-table", "total");
    totaCostColNum = GetColNumber("brouse-items-table", "totalCost");
    selectboxColNum = GetColNumber("brouse-items-table", "s");
    qtyColNum = GetColNumber("brouse-items-table", "qty");

    let tbl = $(".table").find('th').attr('tabindex', -1);
    
    //tbl.find('th').attr('tabindex', -1);

  });
}

function UpdateTableValues() {
  let table = $("#brouse-items-table").DataTable();

  // Iterate over each item in qitemstable
  qitemstable?.forEach(function (qitem) {
    // Find the row index of the matching item in the DataTable
    var rowIndex = table
      .rows()
      .eq(0)
      .filter(function (rowIdx) {
        return table.row(rowIdx).data().SKU === qitem.SKU;
      });

    // If a matching item is found, update its values
    if (rowIndex.length > 0) {
      var tableItem = table.row(rowIndex[0]).data();
      tableItem.Qty = qitem.Qty;
      tableItem.UnitPrice = qitem.UnitPrice;
      tableItem.Total = qitem.Total;
      tableItem.TotalCost = qitem.TotalCost;
      tableItem.S = qitem.Qty > 0;
      
      // Invalidate the row to reflect the changes
      table.row(rowIndex[0]).invalidate();
    }
  });

  // Redraw the entire table after updating all matching items
  table.draw(false);
}

function UpdateTotals() {
  let table = $("#items-table").DataTable();

  let totalItems = table.rows().count();
  let totalQuantity = table
    .column(0)
    .data()
    .reduce(function (acc, val) {
      return acc + parseFloat(val);
    }, 0);

  let totalPrice = table
    .column(7)
    .data()
    .reduce(function (acc, val) {
      return acc + parseFloat(val);
    }, 0);

    var totalCost = table
    .column(9)
    .data()
    .reduce(function (acc, val) {
      return acc + parseFloat(val);
    }, 0);

  $("#totalitems").find("strong").eq(0).text(totalItems);
  $("#totalqty").find("strong").eq(0).text(totalQuantity);
  $("#totalcost").find("strong").eq(0).text(totalCost.toFixed(2));
  $("#totalprice").find("strong").eq(0).text(totalPrice.toFixed(2));

}

function UpdateItems(updatedCell, updatedRow, oldValue) {
  let updatedSKU = updatedRow.data().SKU;
  let updatedQty = updatedRow.data().Qty;
  let updatedUnitPrice = updatedRow.data().UnitPrice;
  let updatedUnitCost = updatedRow.data().UnitCost;


  let updatedTotal = (updatedQty * updatedUnitPrice).toFixed(2);
  let updatedTotalCost = (updatedQty * updatedUnitCost).toFixed(2);
  


  updatedRow.data().Total = updatedTotal;
  updatedRow.data().TotalCost = updatedTotalCost;

  updatedRow.data().S = updatedRow.data().Qty > 0 ? true : false;

  UpdateSelectedPrewiew(updatedRow, selectboxColNum, updatedRow.data().S);
  UpdateTotalPrewiew(updatedRow, totalColNum, updatedTotal);
 // UpdateTotalPrewiew(updatedRow, totaCostColNum, updatedTotalCost);
  UpdateQtyPrewiew(updatedRow, qtyColNum, updatedQty);

  if (updatedQty == 0) {
    qitemstable = qitemstable.filter(function (item) {
      updatedRow.data().Total = 0;
      return item.SKU !== updatedSKU;
    });
  } else {
    let isNeedsUpdated = true;
    qitemstable = qitemstable.map(function (item) {
      
      
      if (item.SKU === updatedSKU) {
        isNeedsUpdated = false;
        return { ...item, Qty: updatedQty };
      }
      return item;


    });

    if (isNeedsUpdated) {
      qitemstable.push(updatedRow.data());
    }
  }
}

function UpdateMainTableItems(updatedCell, updatedRow, oldValue) {
  let updatedQty = updatedRow.data().Qty;
  let updatedUnitPrice = updatedRow.data().UnitPrice;
  let updatedUnitCost = updatedRow.data().UnitCost;
  
  let updatedTotal = (updatedQty * updatedUnitPrice).toFixed(2);
  let updatedTotalCost = (updatedQty * updatedUnitCost).toFixed(2);
  
  updatedRow.data().Total = updatedTotal;
  updatedRow.data().TotalCost = updatedTotalCost;

  updatedRow.data().S = updatedRow.data().Qty > 0 ? true : false;

  UpdateTotalPrewiew(updatedRow, MaintotalColNum, updatedTotal);
 // UpdateTotalPrewiew(updatedRow, MaintotalCostColNum, updatedTotalCost);

  
  UpdateTotals();
}

function UpdateTotalPrewiew(updatedRow, totalColNum, updatedTotal) {
  updatedRow.node().getElementsByTagName("td")[totalColNum].textContent =
    updatedTotal;
}

function UpdateSelectedPrewiew(updatedRow, selectboxColNum, updatedValue) {
  updatedRow
    .node()
    .getElementsByTagName("td")
    [selectboxColNum].querySelector('input[type="checkbox"]').checked =
    updatedValue;
}

function UpdateQtyPrewiew(updatedRow, qtyColNum, updatedQty) {
  updatedRow
    .node()
    .getElementsByTagName("td")
    [qtyColNum].querySelector('input[type="number"]').value = updatedQty;
}

function CopyItemsFromQuotation() {
  if (IsGroupItems()){
    qitemstable = [];
    itemsTable = $("#items-table").DataTable().rows().data().toArray();

    qitemstable = itemsTable.reduce((acc, item) => {
  
      const existingItemIndex = acc.findIndex(existingItem => existingItem.SKU === item.SKU);
      if (existingItemIndex !== -1) {
      
        acc[existingItemIndex] = item;
      } else {
   
        acc.push(item);
      }
      return acc;
    }, []);
  }
  else
  {
    qitemstable=[];
  }
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



function GetColNumber(tablename, colname) {
  let table = document.getElementById(tablename);
  let headerRow = table.rows[0];
  let totalIndex = Array.from(headerRow.cells).findIndex(
    (cell) => cell.textContent.trim().toLowerCase() === colname.toLowerCase()
  );
  return totalIndex;
}

function AddAdditionalColumns(items, qty = 0) {
  items.data.forEach(function (item) {
    item.Qty = qty;
    item.Total = item.Qty * item.UnitPrice;
    item.TotalCost =  item.Qty * item.UnitCost;
    item.Comment = "";
    item.S = false;
  });
  return items;
}

function CheckItemInQuatation(SKU) {
  var tableData = $("#items-table").DataTable().rows().data().toArray();
  return tableData.filter(function (item) {
    return item.SKU === SKU;
  });
}

$("#addItemButton").click(function () {
  MoveToMainTable();
});


$("#quickSearchButton").click(function () {
  ChangeQuickSearchParametr();
});

function ChangeQuickSearchParametr() {
 let button = $("#quickSearchButton");

  if (button.val() === "[F2] SKU") {
    button.val("[F2] UPC");
    button.attr("data-id", "2");
  } else {
    button.val("[F2] SKU");
    button.attr("data-id", "1");
  }
}


$("#exampleModal").on("hidden.bs.modal", function () {
  CleanSearch("");
  CleanDatable("#brouse-items-table");
});



function MoveToMainTable() {
  var table = $("#items-table").DataTable();
  if (IsGroupItems()){
    qitemstable.forEach(item => {
      const existingIndex = table.rows().indexes().toArray().reverse().find(index => {
        const rowData = table.row(index).data();
        return rowData && rowData.SKU === item.SKU;
      });
    
      if (existingIndex !== undefined) {       
        table.row(existingIndex).data(item).draw();
      } 
      else 
      {
       
        table.row.add(item).draw();
      }
    });    
  }
  else
  {
    table.rows.add(qitemstable).draw();
  }

  $("#exampleModal").modal("hide");
  InitMainTableQty();
  InitMainTableUnitPrice();
  InitMainTableComment();
  UpdateTotals();
}

function InitCheckboxes() {
  // Get all the checkboxes in the first column
  const checkboxes = document.querySelectorAll(
    '#brouse-items-table tbody tr td:first-child input[type="checkbox"]'
  );

  // Loop through each checkbox and attach a change event listener
  checkboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", function () {
      let table = $("#brouse-items-table").DataTable();

      let closestRow = $(this).closest("tr");
      let row = table.row(closestRow);
      row.data().Qty = this.checked ? 1 : 0;
      UpdateItems(null, row, null);
    });
  });
}

function InitQty() {
  const numberInputs = document.querySelectorAll(
    '#brouse-items-table tbody tr td:nth-child(2) input[type="number"]'
  );

  // Loop through each checkbox and attach a change event listener
  numberInputs.forEach((num) => {

    num.addEventListener("click", function () {
      // Select all the content of the input field
      this.select();
    });




    num.addEventListener("change", function () {
      let table = $("#brouse-items-table").DataTable();

      let closestRow = $(this).closest("tr");

      let row = table.row(closestRow);

      row.data().Qty = this.value;

      UpdateItems(null, row, null);
    });
  });
}

function InitUnitPrice() {
  const numberInputs = document.querySelectorAll(
    '#brouse-items-table tbody tr td:nth-child(4) input[type="number"]'
  );
  // Loop through each checkbox and attach a change event listener
  numberInputs.forEach((num) => {
    num.addEventListener("change", function () {
      let table = $("#brouse-items-table").DataTable();

      let closestRow = $(this).closest("tr");

      let row = table.row(closestRow);

      row.data().UnitPrice = this.value;

      UpdateItems(null, row, null);
    });
  });
}
///init main table
function InitMainTableQty() {
 
  const numberInputs = document.querySelectorAll(
    '#items-table tbody tr td:nth-child(1) input[type="number"]'
 
    );

    
  // // Loop through each checkbox and attach a change event listener
  numberInputs.forEach((num) => {

    num.addEventListener("click", function () {
      // Select all the content of the input field
      this.select();
    });

    num.addEventListener("change", function () {
      let table = $("#items-table")?.DataTable();

      let closestRow = $(this).closest("tr");

      let row = table.row(closestRow);

      row.data().Qty = this.value;

      UpdateMainTableItems(null, row, null);
    });
  });
}

function InitMainTableUnitPrice() {
  const numberInputs = document.querySelectorAll(
    '#items-table tbody tr td:nth-child(3) input[type="number"]'
  );
  // Loop through each checkbox and attach a change event listener
  numberInputs.forEach((num) => {
    num.addEventListener("change", function () {
      let table = $("#items-table").DataTable();

      let closestRow = $(this).closest("tr");
      let row = table.row(closestRow);

      row.data().UnitPrice = this.value;

      UpdateMainTableItems(null, row, null);
    });
  });
}

function InitMainTableComment() {
  const textInputs = document.querySelectorAll(
    '#items-table tbody tr td:nth-child(6) input[type="text"]'
  );
  // Loop through each checkbox and attach a change event listener
  textInputs.forEach((num) => {
    num.addEventListener("change", function () {
      let table = $("#items-table").DataTable();

      let closestRow = $(this).closest("tr");
      let row = table.row(closestRow);
      row.data().Comment = this.value;

    });
  });
}

function CleanDatable(tabelId) {
  if ($.fn.dataTable.isDataTable(tabelId)) {
    table = $(tabelId).DataTable();
    $(tabelId).DataTable().clear().draw();
  } else {
    table = $(tabelId).DataTable({
      paging: false,
    });
  }
  table.destroy();
}

function CleanSearch(searchid) {
  $("#modalsearch").val("");
}



function GetDropdownValue(dropdownSelector) {
  //TODO temp should be numeric value
  //let selectedValue = $(dropdownSelector).data().value;
  let selectedValue = String($(dropdownSelector).attr("data-value"));
  let selectedText = $(dropdownSelector).text().trim();
  let jsonData = {
    searchById: selectedValue,
    searchBy: selectedText,
  };
  return jsonData;
}

function initBrowseTable(inputValue) {
  if (inputValue.length >= 3) {
    BrouseItems()
      .then(function () {
        InitCheckboxes();
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

function SetTodayDate() {
  let today = new Date();
  let day = today.getDate();
  let month = today.getMonth() + 1;
  let year = today.getFullYear();

  if (day < 10) {
    day = "0" + day;
  }

  if (month < 10) {
    month = "0" + month;
  }
  let formattedDate = year + "-" + month + "-" + day;

  $("#qdate")?.val(formattedDate);
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

async function SetAdditionalFilds() {
  let data = await GetAdditionalInfo();

  Object.entries(data).forEach(([fieldName, fieldValue]) => {
    // Create dropdown for the current field
    if (Array.isArray(fieldValue)) {

      CreateDropdowns(fieldName + "DropDown", fieldValue);
    }
  });

 await GetQuotation();

 if ((!$('#qnumber')?.val())){
  ChangeSalesRep(data['currentSalesRep'],data['salesRep']);
 }

 
}

function initResetShipButton() {
  $("#resetShip").click(function () {
    $("#sstreet").val("");
    $("#sstreet2").val("");
    $("#scity").val("");
    $("#sstate").val("");
    $("#szip").val("");
    $("#scname").val("");
    $("#sphone").val("");
  });
}

function initCopyButton() {
  $("#copyButton").click(function () {
    $("#sstreet").val($("#bstreet").val());
    $("#sstreet2").val($("#bstreet2").val());
    $("#scity").val($("#bcity").val());
    $("#sstate").val($("#bstate").val());
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

function ShowCustomerMemo(message){
   toastr.clear();
   toastr.remove();
  if (message === null || message === undefined || /^\s*$/.test(message)){
    message = "There are no customer's memo!"
  }
  toastr.info(message, 'Customer Memo', {
    "tapToDismiss":false,
    "closeButton": true,
    "debug": false,
    "newestOnTop": false,
    "progressBar": false,
    "positionClass": "toast-top-right",
    "preventDuplicates": false,    
    "showDuration": "300",
    "hideDuration": "0",
    "timeOut": "-1", 
    "extendedTimeOut": "-1", 
    "showEasing": "swing",
    "hideEasing": "linear",
    "showMethod": "fadeIn",
    "hideMethod": "fadeOut"
});

}


function removeRow() {
  var table = $("#items-table").DataTable();
  var selectedRows = table.rows({ selected: true }).indexes();
  selectedRows.each(function (index) {
    table.row($(this)).remove().draw(false);
  });
}

$(document).on("keydown", function (e) {
  if (e.key === "Delete") {
    removeRow();
    UpdateTotals();
  }
});

///search
$("#bnameInput").on("input", async function (event) {
  var inputValue = $(this).val();
  await initBusness(inputValue, $(this).attr("id"));
});

$("#acnumInput").on("input", async function (event) {
  var inputValue = $(this).val();
  await initBusness(inputValue, $(this).attr("id"));
});

async function initBusness(inputValue, name) {
  if (inputValue.length >= 2) {   
      autocomplete(document.getElementById(name));
  }
}



$(document).ready(function () {
  $("#quicksearch").on("keypress", function (event) {
    if (event.which === 13) {
      event.preventDefault();

      QuickSearch()
        .then(function (response) {
          AddQuickSearchItem(response);
        })
        .catch(function (error) {
          console.error(error);
        });
    }
  });
});

function AddQuickSearchItem(items) {


  if (items?.data?.length > 0) {
    let table = AddAdditionalColumns(items, (qty = 1));
    MoveQuickSearch(table?.data[0]);
  }



}

function MoveQuickSearch(item) {
  let table = $("#items-table").DataTable();
  

  if (!IsGroupItems()){

    let itemsArray = [item];
    table.rows.add(itemsArray).draw();
  }
  else
  {
    let items = table.rows().data().toArray();
    
     let lastItem = items.findLast(element=>element.SKU===item.SKU);

     if (lastItem) {       
         lastItem.Qty += 1;
         let index = items.findLastIndex(element => element.SKU === lastItem.SKU);
       
         if (index !== -1) {
             table.row(index).data(lastItem).draw();
         }
        
     }
     else{
      let itemsArray = [item];
      table.rows.add(itemsArray).draw();
     }



  }


  InitMainTableQty();
  InitMainTableUnitPrice();
  InitMainTableComment();
  UpdateTotals();
}

function QuickSearch() {
  return GetQuickSearchItem();
}

function autocomplete(inp) {
  /*the autocomplete function takes two arguments,
  the text field element and an array of possible autocompleted values:*/
  var currentFocus;
  /*execute a function when someone writes in the text field:*/

   
  inp.addEventListener("click",async function(e){
    val = this.value;    
    let jsonData= await GetBusneessInfo(val, this.id);
    if (jsonData.data.length > 0) {
      ProcessAutoComplite(val,inp,jsonData);
    }
  });

  inp.addEventListener("input", async function (e) {
    val = this.value;    
    let jsonData= await GetBusneessInfo(val, this.id);
    if (jsonData.data.length > 0) {
      ProcessAutoComplite(val,inp,jsonData);
    }  
  });

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




  function ProcessAutoComplite(val,inp,arr){

    var a,
      b,
      i;
   
    /*close any already open lists of autocompleted values*/
    CloseAllLists();
    if (!val) {
      return false;
    }
    currentFocus = -1;
    /*create a DIV element that will contain the items (values):*/
    a = document.createElement("DIV");
    a.setAttribute("id", this.id + "autocomplete-list");
    a.setAttribute("class", "dropdown-menu show selectopened");

    a.style.maxHeight = "240px";
    a.style.overflowY = "auto";
    /*append the DIV element as a child of the autocomplete container:*/
    inp.parentNode.appendChild(a);
    /*for each item in the array...*/
    let foundMatch = false;

    for (i = 0; i < arr?.data.length; i++) {
      /*check if the item starts with the same letters as the text field value:*/
      // if (arr.data[i].bname.substr(0, val.length).toUpperCase() == val.toUpperCase()) {
      /*create a DIV element for each matching element:*/

      b = document.createElement("DIV");
      b.setAttribute("class", "dropdown-item");
      /*make the matching letters bold:*/

      if (inp?.id == "acnumInput") {
        b.innerHTML =
          "<strong>" + arr.data[i].anum.substr(0, val.length) + "</strong>";
        b.innerHTML += arr.data[i].anum.substr(val.length);

        /*insert a input field that will hold the current array item's value:*/
        b.innerHTML +=
          "<input type='hidden' id='" +
          arr.data[i].id +
          "' value='" +
          arr.data[i].anum +
          "'>";
      } else {
        b.innerHTML = "<a>"+
          "<strong>" + arr.data[i].bname.substr(0, val.length) + "</a>";
        b.innerHTML += "<a>"+ arr.data[i].bname.substr(val.length) +"</a>"  ;
    

        /*insert a input field that will hold the current array item's value:*/
        b.innerHTML +=
          "<input type='hidden' id='" +
          arr.data[i].id +
          "' value='" +
          arr.data[i].bname +
          "'>";
        /*execute a function when someone clicks on the item value (DIV element):*/
      }

      b.addEventListener("click", function (e) {
        /*insert the value for the autocomplete text field:*/
        inp.value = this.getElementsByTagName("input")[0].value;
        let id = this.getElementsByTagName("input")[0].id;
        if (inp?.id == "bnameInput") {
          AssignBusnessAcc(id, arr);
        } else {
          AssignAccNum(id, arr);
        }

        FillAddresesAndMemo(id, arr);   
        CloseAllLists();
      });
      a.appendChild(b);
      foundMatch = true;
      // }

      if (!foundMatch) {
        a.style.display = "none";
      }
    }
  }


  function addActive(x) {
    /*a function to classify an item as "active":*/
    if (!x)
    {
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
    var bnameInput = document.getElementById('bnameInput');
    var acnumInput = document.getElementById('acnumInput');

   
    if (e.target !== bnameInput && e.target !== acnumInput && !bnameInput.contains(e.target) && !acnumInput.contains(e.target)) {
        CloseAllLists(e.target);
    }
});
}

function AssignBusnessAcc(id, arr) {
  var foundItem = arr.data.find(function (item) {
    return item.id == id;
  });
  $("#acnumInput").attr("data-id",foundItem.id);
  $("#acnumInput").val(foundItem.anum);
}

function AssignAccNum(id, arr) {
  var foundItem = arr.data.find(function (item) {
    return item.id == id;
  });
  $("#bnameInput").val(foundItem.bname);
  $("#bnameInput").attr("data-id",foundItem.id);
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

function FillTerms(termsid){ 
  
  let text = $("#termsdropdown-menu").find("[data-value='" + termsid.toString() + "']").text();
  $("#terDropdown").text(text);
  $("#terDropdown").attr("data-value",termsid.toString());
    
}

function FillSalesRep(srepid){ 
  
  let text = $("#srepdropdown-menu").find("[data-value='" + srepid.toString() + "']").text();
  $("#srepDropdownButton").text(text);
  $("#srepDropdownButton").attr("data-value",srepid.toString());
    
}


function FillShipVia(shipviaid){ 
  
  let text = $("#shipviadropdown-menu").find("[data-value='" + shipviaid.toString() + "']").text();
  $("#shipviaDropdownButton").text(text);
  $("#shipviaDropdownButton").attr("data-value",shipviaid.toString());
    
}

function FillBilling(foundItem) {
  $("#bstreet").val(foundItem.billingAddress.street);
  $("#bstreet2").val(foundItem.billingAddress.street2);
  $("#bcity").val(foundItem.billingAddress.city);
  $("#bstate").val(foundItem.billingAddress.state);
  $("#bzip").val(foundItem.billingAddress.zip);
  $("#bcname").val(foundItem.billingAddress.contactName);
  $("#bphone").val(foundItem.billingAddress.phone);
}

function FillShipping(foundItem) {
  $("#shipName").val(foundItem.shippingAddress.shipName);
  $("#sstreet").val(foundItem.shippingAddress.street);
  $("#sstreet2").val(foundItem.shippingAddress.street2);
  $("#scity").val(foundItem.shippingAddress.city);
  $("#sstate").val(foundItem.shippingAddress.state);
  $("#szip").val(foundItem.shippingAddress.zip);
  $("#scname").val(foundItem.shippingAddress.contactName);
  $("#sphone").val(foundItem.shippingAddress.phone);
}

function PrepareMainFields() {
  return {
    DB: sessionStorage.getItem("modelDop"),
    qnumber: $("#qnumber").val(),
    qdate: $("#qdate").val(),

    accountnum: $("#acnumInput").val(),
    businessname: $("#bnameInput").val(),
    CustomerID:$("#acnumInput").attr('data-id'),

    srep: parseInt($("#srepDropdownButton").attr("data-value")||0),

    shipto:$("#shipName").val(),

    sstreet: $("#sstreet").val(),
    sstreet2: $("#sstreet2").val(),
    scity: $("#scity").val(),
    sstate: $("#sstate").val(),
    szip: $("#szip").val(),
    scname: $("#scname").val(),
    sphone: $("#sphone").val(),
    
    shipvia: parseInt($("#shipviaDropdownButton").attr("data-value") ||0),
    terms: parseInt($("#terDropdown").attr("data-value") ||0),

    bstreet: $("#bstreet").val(),
    bstreet2: $("#bstreet2").val(),
    bcity: $("#bcity").val(),
    bstate: $("#bstate").val(),
    bzip: $("#bzip").val(),
    bcname: $("#bcname").val(),
    bphone: $("#bphone").val(),
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

function AssignQuotationNumber(number){
  $('#qnumber').val(number); 
}

function ChangeToEditFields(){
  
   
  $('#removeButton').removeAttr('disabled');   


   if ($('#QuotationID').val() && !$('#InvoiceID').val()){
     $('#ConvertButton').removeAttr('disabled');  
   }




  $('#labelH1').text('EDIT QUOTATION');

}


function ValidateForm() {
  let accountnum = $("#acnumInput");
  let businessname = $("#bnameInput");
  let srep = $("#srepDropdownButton");
  let srepValue = parseInt(srep.attr("data-value") || 0);
  let errors = [];

 
  if (!accountnum.val()) {
      errors.push("Field 'Account Number' is not filled.");
      accountnum.addClass('invalid-input');
  } else {
      accountnum.removeClass('invalid-input');
  }
  if (!businessname.val()) {
      errors.push("Field 'Business Name' is not filled.");
      businessname.addClass('invalid-input');
  } else {
      businessname.removeClass('invalid-input');
  }
  if (srepValue === 0) {
      errors.push("Field 'Sales Rep' should be selected.");
      srep.addClass('invalid-input');
  } else {
      srep.removeClass('invalid-input');
  }
  
  if (errors.length > 0) {
      //toastr.error("Validation error(s):");
      errors.forEach(function(error) {
          toastr.error(error);
      });
      return false; 
  }

  return true; 
}

function PopulateQuotationDetails(data){

  $('#qnumber').val(data.qnumber);  
  $('#QuotationID').val(data?.QuotationID??'');
  $('#InvoiceID').val(data?.InvoiceID??'');

  // Assuming data.qdate is "04-04-2024"
  var parts = data.qdate.split('-');
  var formattedDate = parts[2] + '-' + parts[1] + '-' + parts[0]; // Rearrange to yyyy-MM-dd format

  // Alternatively, you can use the Date object to parse and format the date
  var dateObj = new Date(parts[2], parts[1] - 1, parts[0]); // Months are 0-indexed in JavaScript
  formattedDate = dateObj.toISOString().split('T')[0]; // Get the ISO format yyyy-MM-dd

// Set the value of the input field
  $('#qdate').val(formattedDate)



   $("#bnameInput").val(data.businessname);
   $("#bnameInput").attr("data-id",data.CustomerID);

   $("#acnumInput").val(data.accountnum);
   $("#acnumInput").attr("data-id",data.CustomerID);

   FillTerms(data.terms);
   FillSalesRep(data.srep);  
   FillShipVia(data.shipvia);
   $('#shipName').val(data.shipto);
   $('#sstreet').val(data.sstreet);
   $('#sstreet2').val(data.sstreet2);
   $('#scity').val(data.scity);
   $('#sstate').val(data.sstate);
   $('#szip').val(data.szip);
   $('#scname').val(data.scname);
   $('#sphone').val(data.sphone);
   $('#bstreet').val(data.bstreet);
   $('#bstreet2').val(data.bstreet2);
   $('#bcity').val(data.bcity);
   $('#bstate').val(data.bstate);
   $('#bzip').val(data.bzip);
   $('#bcname').val(data.bcname);
   $('#bphone').val(data.bphone);
   
   var tableData = [];

data.items.forEach(function(item) {
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
}


function ConvertQuotation(){

  let DBname = sessionStorage.getItem("modelDop");
  let QuotationID = $('#QuotationID').val();
  let QuotationNumber =$('#qnumber').val();

    let paramsObj = {
        DBname: DBname,
        QuotationID: QuotationID,    
        QuotationNumber: QuotationNumber    
    };


    ShowConvertModal(paramsObj);
    
}

///prevent focus in modal
$('#exampleModal').on('shown.bs.modal', function () {  
   BrouseItems();
  $('#modalsearch').focus(); 

});

$('#exampleModal').on('keydown', function(e) {

  if (e.key === 'Tab' || e.keyCode === 9) {
     
      var focusableElements = $('#exampleModal').find('input:visible, button:visible, select:visible, textarea:visible, [tabindex]:visible').not('input.form-check-input .btn-close, thead *').not('.btn-close').not('.form-check-input').not('.btn');
      var currentIndex = focusableElements.index(document.activeElement);

     
      if (e.shiftKey && currentIndex === 0) {
          focusableElements = focusableElements.not('thead *, thead');
          e.preventDefault();
      }else if 
      (!e.shiftKey && (currentIndex === focusableElements.length - 1)) {
        $('#exampleModal').find('input, button, select, textarea, [tabindex]').not('.btn-close, thead *').not('.btn-close').not('.form-check-input').first().focus().select();
        e.preventDefault();
    }
      
  }

  if ((e.key === 'Escape' || e.keyCode === 27 || e.keyCode===114)&& $("#brouse-items-table").DataTable().data().length<=0) {
    $('#exampleModal').modal('hide');
  }
  
  if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.keyCode === 75))  {
    MoveToMainTable();
  }


});

//modal search select value on click
$('#modalsearch').on('click', function() {

  if ($(this).val()) {
     
      $(this).select();
  }
});

function ChangeSalesRep(salesRepName,salesRepArray ){
    let salesRepObj = salesRepArray.find(rep => rep.name.toLowerCase() === salesRepName.toLowerCase())

    if(salesRepObj){
      $("#srepDropdown").text(salesRepObj.name);
      $("#srepDropdown").attr("data-value", salesRepObj.id);
      
      $('#srepDropdownButton').text(salesRepObj.name);
      $('#srepDropdownButton').attr("data-value", salesRepObj.id); 
    }
    else
    {
      $("#srepDropdown").text("");
      $("#srepDropdown").attr("data-value", "");
      
      $('#srepDropdownButton').text("Select Sales Rep");
      $('#srepDropdownButton').attr("data-value", ""); 
    } 


}

function IsGroupItems(){
  return $('#groupitems')?.prop('checked')?? false; 
}


$(document).keydown(function(event) {
  if (event.which === 113) { // F2
    ChangeQuickSearchParametr();
   }

   if (event.which === 114) { // F3
    CopyItemsFromQuotation();
    $('#exampleModal').modal('show');
   }
// ctrl+K
});