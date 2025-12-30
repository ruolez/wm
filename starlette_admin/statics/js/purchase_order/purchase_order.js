var mainitemstable;
var totalColNum;
var selectboxColNum;
var qtyColNum;
let selectedModelId = GetDb();
var MaintotalColNum;
var MaintotalCostColNum;
var totaCostColNum;
var ProfitMarginColNum;

document.addEventListener("DOMContentLoaded", function () {
  inDataTable();
});

$(document).ready(function () {

  toastr.options = {
    closeButton: true,
    debug: false,
    newestOnTop: false,
    progressBar: true,
    positionClass: "toast-top-right",
    preventDuplicates: false,
    onclick: null,
    showDuration: "300",
    hideDuration: "1000",
    timeOut: "5000",
    extendedTimeOut: "1000",
    showEasing: "swing",
    hideEasing: "linear",
    showMethod: "fadeIn",
    hideMethod: "fadeOut",
  };

  SetDbDropDown();
  // InitDataTable();
  SetTodayDate("#podate");
  //SetDbDropDown();
  if (GetDb()) {
    SetAdditionalFilds();
  }
  $("#dropdownMenu").on("click", ".dropdown-item", function () {
    SetAdditionalFilds();

  });
  ChangeToEditFields();

});





///search
$("#bnameInput").on("input", Debounce(async function (event) {
  var inputValue = $(this).val();
  await initBusness(inputValue, $(this).attr("id"));
}, 300));

$("#acnumInput").on("input", Debounce(async function (event) {
  var inputValue = $(this).val();
  await initBusness(inputValue, $(this).attr("id"));
}, 300));

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

async function initBusness(inputValue, name) {
  autocomplete(document.getElementById(name));
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

    jsonData = await GetBusneessInfo(val, this.id);

    if (jsonData.data.length > 0) {
      ProcessAutoComplite(val, inp, jsonData);
      SetDBDropDown(!CheckDBBlock());
    }
  });

  inp.addEventListener("input", Debounce(async function (e) {
    val = this.value;
    let jsonData = [];

    jsonData = await GetBusneessInfo(val, this.id);

    if (jsonData.data.length > 0) {
      this.setAttribute('data-id', '');
      ProcessAutoComplite(val, inp, jsonData);
      SetDBDropDown(!CheckDBBlock());
    }
  }, 300));

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

      }


      if (inp.getAttribute('data-id')) {
        SetDBDropDown();
      } else {
        if (inp?.id == "bnameInput") {
          $("#acnumInput").val('');
          SetDBDropDown(false);
        }
        else if (inp?.id == "acnumInput") {
          $("#bnameInput").val('');
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
    if (!val) {
      if (inp?.id == "acnumInput") {
        $('#bnameInput').val('');
      } else if (inp?.id == "bnameInput") {
        $('#acnumInput').val('');
      }

      SetDBDropDown(CheckDBBlock());
      ResetContact();
      return false;
    } else {
      if (inp.getAttribute('data-id')) {
        SetDBDropDown();
      }
      else {
        if (inp?.id == "bnameInput") {
          $("#acnumInput").val('');
          SetDBDropDown(false);
        }
        else if (inp?.id == "acnumInput") {
          $("#bnameInput").val('');
          SetDBDropDown(false);
        }
      }
    }

    //SetDBDropDown(CheckDBBlock());

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

      let shouldAddAutoCompleteItem = true;



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



}

async function GetBusneessInfo(inputValue, name) {
  return new Promise((resolve, reject) => {
    let searchData = {
      DB: GetDb(),
      searchBy: name,
      searchValue: inputValue,
    };

    $.ajax({
      url: model.apiUrl + "/getbusinessinfo",
      type: "POST",
      data: searchData,
      traditional: true,
      dataType: "json",
      success: function (response) {
        resolve(response);
      },
      error: function (xhr, status, error) {
        reject(error);
      },
    });
  });
}

function FillAddresesAndMemo(id, arr) {
  var foundItem = arr.data.find(function (item) {
    return item.id == id;
  });

  if (foundItem) {
    FillCustomerMemo(foundItem);
  }
}

function FillCustomerMemo(foundItem) {
  $("#contactname").val(foundItem.Contactname);
  $("#bphone").val(foundItem.Phone_Number);
}

function ResetContact() {
  $("#contactname").val('');
  $("#bphone").val('');
}

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
          var isDisabled = $('#status').val() == 1 ? 'disabled' : '';

          return (
            '<input class="form-control m-0 form-control-table unsetbackground form-control-table focusable columnOne" type="number" value="' +
            data +
            '" min="0" ' + isDisabled + '>'
          );
        },
        className: "td-wrapper unsetbackground",
      },
      { data: "Description" },

      {
        data: "UnitCost",
        render: function (data, type, row) {

          var isDisabled = $('#status').val() == 1 ? 'disabled' : '';

          return (
            '<input tabindex="-1" class="form-control m-0 form-control-table unsetbackground form-control-table focusable columnTwo" type="number" value="' +
            parseFloat(data).toFixed(2) +
            '" min="0.00" step="0.01" ' + isDisabled + '>'
          );

        },
        className: "td-wrapper",
      },

      { data: "UnitPrice" },

      { data: "SKU" },
      { data: "UPC" },
      {
        data: "Stock",
        orderable: false,
      },
      {
        data: "Total",
        title: "Total",
        render: function (data, type, row) {
          return parseFloat(data).toFixed(2);
        }
      },
      {
        data: "Comment",
        orderable: false,
        render: function (data, type, row) {
          return (
            '<input tabindex="-1" class="form-control m-0 form-control-table unsetbackground width100 form-control-table"type="text" value=""' +
            parseFloat(data).toFixed(2) +
            '" min="0.00"step="0.01" >'
          );;
        },
        className: "td-wrapper",
      },
      {
        data: "TotalCost",
        title: "Total Cost",
        render: function (data, type, row) {
          return parseFloat(data).toFixed(2);
        },
        className: "text-center price-column",
      },
      {
        orderable: false,
        render: function (data, type, row) {
          var isDisabled = $('#status').val() == 1 ? 'disabled' : '';

          return '<button tabindex="-1" onclick="removerow(event, \'PO\')"  class="btn btn-danger w-100 btn-icon btn-sm" ' + isDisabled + '>' +
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
        width: "10%",
      },
      {
        target: 1,
        visible: true,
        width: "67%",
      },
      {
        target: 2,
        visible: true,
        //  width: "10%",
      },
      {
        target: 3,
        visible: false,
        width: "10%",
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
        visible: false,
        // width: "10%",
      },
      {
        target: 7,
        visible: false,

      },
      {
        target: 8,
        visible: false,
        // width: "25%",
      },
      {
        target: 9,
        visible: true,
        width: "10%"
      },
      {
        target: 9,
        visible: true,
        width: "3%",
      },
    ],
  });
  // $("#items-table thead th").css("font-size", "10px");
  table.MakeCellsEditable({
    columns: [0],
    onUpdate: UpdateMainTableItems,
  });
  MaintotalColNum = GetColNumber("items-table", "total");
  MaintotalCostColNum = GetColNumber("items-table", "total Cost");
}

async function SetAdditionalFilds() {
  await GetPO();
  if ($("#POID").val()) {
    SetDBDropDown(true);
  }
}


function ChangeToEditFields() {
  $('#removeButtonWrapper').addClass('modal-blur-bg');
  $('#actionButtonsWrapper').addClass('modal-blur-bg');

  $('#submitAndSaveButton').removeAttr('disabled');
  $('#submitButton').removeAttr('disabled');
  $('#printButton').removeAttr('disabled');
  $('#ConvertButton').removeAttr('disabled');
  $('#removeButton').removeAttr('disabled');
  $('#searchPanel').css('opacity', '1');
  $('#searchPanel').css('pointer-events', 'All');


  // Check if POID and status are set
  if ($('#POID').val()) {
    // Get the value of the status field
    var status = $('#status').val();
    $('#labelH1').text('EDIT PURCHASE ORDER');
    // If status is not '1', enable all buttons
    if (status != '1') {
      $('#submitAndSaveButton').removeAttr('disabled');
      $('#submitButton').removeAttr('disabled');
      $('#ConvertButton').removeAttr('disabled');
      $('#removeButton').removeAttr('disabled');
    } else {
      // If status is '1', disable all buttons except the print button
      $('#submitAndSaveButton').attr('disabled', 'disabled');
      $('input').prop('disabled', true);

      $('#submitButton').attr('disabled', 'disabled');
      $('#ConvertButton').attr('disabled', 'disabled');
      $('#removeButton').attr('disabled', 'disabled');
      $('#searchPanel').css('opacity', '0.5');
      $('#searchPanel').css('pointer-events', 'none');
      $('#printButton').text('Print');



    }
  }
  else {
    // If there is no POID, disable all buttons except save and print buttons
    $('#ConvertButton').attr('disabled', 'disabled');
    $('#removeButton').attr('disabled', 'disabled');
  }

  if (!isCommitAllowed) {
    $('#ConvertButton').attr('disabled', 'disabled');
  }

  // Remove blur class after all operations are completed
  setTimeout(function () {
    $('#removeButtonWrapper').removeClass('modal-blur-bg');
    $('#actionButtonsWrapper').removeClass('modal-blur-bg');
  }, 300);
}

///only for PO, other should be have different implementation
function InitMainTableUnitCost() {
  const numberInputs = document.querySelectorAll(
    '#items-table tbody tr td:nth-child(3) input[type="number"]'
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
      row.data().UnitCost = this.value;
      UpdateMainTableItems(null, row, null);
    });
  });
}



function InitTableUnitCost() {
  const numberInputs = document.querySelectorAll('#browse-items-table tbody tr td:nth-child(5) input[type="number"]');


  // // Loop through each checkbox and attach a change event listener
  numberInputs.forEach((num) => {

    num.addEventListener("click", function () {
      // Select all the content of the input field
      this.select();
    });

    num.addEventListener("change", function () {
      let table = $("#browse-items-table")?.DataTable();
      let closestRow = $(this).closest("tr");
      let row = table.row(closestRow);
      row.data().UnitCost = this.value;
      if (row.data().Qty <= 0) {
        row.data().Qty = 1;
      }
      UpdateItems(null, row, null);
    });
  });
}


async function GetBrowseItems(inputValue) {
  let lookinValue = GetDropdownValue("#lookinDropdown");
  let searchData = {
    DB: GetDb(),
    searchValue: inputValue,
    anum: $("#acnumInput").val() || "",
    isStockRequested: 0,
    ignoreaccout: 1
  };

  searchData = Object.assign({}, searchData, lookinValue);

  try {
    let response = await $.ajax({
      url: model.apiUrl + "/browseitems",
      type: "POST",
      data: searchData,
      traditional: true,
      dataType: "json",
    });
    return response;
  } catch (error) {
    throw error;
  }
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
      ajax: function (data, callback, settings) {
        var inputValue = $("#modalsearch").val();
        if (inputValue?.length > 2) {

          GetBrowseItems(ReplaceSpace(inputValue))
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
              '<input class="form-control m-0 form-control-table width100 focusable columnOne"type="number" value="' +
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
            return parseFloat(data).toFixed(2);
          },
          className: "text-center price-column",
        },
        {
          data: "UnitCost",
          render: function (data, type, row) {
            return (
              '<input tabindex="-1" class="form-control m-0 form-control-table width100 focusable columnTwo" type="number" value="' +
              parseFloat(data).toFixed(2) +
              '" min="0.00" step="0.01">'
            );
          },
          className: "td-wrapper unitPrice p-0",
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
        },
        {
          data: "Total",
          render: function (data, type, row) {
            return parseFloat(data).toFixed(2);
          },
          className: "text-center price-column",
        },
        {
          data: "TotalCost",
          render: function (data, type, row) {
            return parseFloat(data).toFixed(2);
          },
          className: "text-center price-column",
        },
        {
          data: "Comment",
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
          visible: false,
          width: "10%",
        },
        {
          target: 8,
          visible: false,

        },
        {
          target: 9,
          visible: true,
          width: "14%",
          className: "total-column",
          render: function (data, type, row, meta) {
            return type === "display" && typeof data === "number"
              ? parseFloat(data).toFixed(2)
              : data;
          },
        },
        {
          target: 10,
          visible: false,

        },
      ]

      //order: [[2, "asc"]],
    });

    table.MakeCellsEditable({
      columns: [0, 1, 5],
      onUpdate: UpdateItems,
    });

    totalColNum = GetColNumber("browse-items-table", "total");
    totaCostColNum = GetColNumber("browse-items-table", "totalCost");
    selectboxColNum = GetColNumber("browse-items-table", "s");
    qtyColNum = GetColNumber("browse-items-table", "qty");

    let tbl = $(".table").find('th').attr('tabindex', -1);

  });
}


function Commit() {

  let DBname = GetDb();
  let POId = $('#POID').val();
  let ponumber = $('#ponumber').val();

  let paramsObj = {
    DBname: DBname,
    POId: POId,
    PoNumber: ponumber,
    status: 1
  };
  ShowCommitModal(paramsObj, null, true);

}

function QuickSearchPO() {
  return GetQuickSearchItem(0);
}


$(document).ready(function () {
  $("#quicksearch").on("keypress", function (event) {
    if (event.which === 13) {
      event.preventDefault();

      QuickSearchPO()
        .then(function (response) {
          AddQuickSearchItemPO(response);
          SetDBDropDown(CheckDBBlock());
        })
        .catch(function (error) {
          console.error(error);
        });
    }
  });
});

function AddQuickSearchItemPO(items) {


  if (items?.data?.length > 0) {
    let table = AddAdditionalColumns(items, (qty = 1));
    MoveQuickSearchPO(table?.data[0]);
    $('#items-table').parent().removeClass('invalid-input');

  }

}

function MoveQuickSearchPO(item) {
  let table = $("#items-table").DataTable();




  if (!IsGroupItems()) {

    let itemsArray = [item];
    table.rows.add(itemsArray).draw();
  }
  else {
    let items = table.rows().data().toArray();

    let lastItem = items.findLast(element => element.SKU === item.SKU);

    if (lastItem) {
      lastItem.Qty += 1;
      let index = items.findLastIndex(element => element.SKU === lastItem.SKU);

      if (index !== -1) {
        table.row(index).data(lastItem).draw();
      }

    }
    else {
      let itemsArray = [item];
      table.rows.add(itemsArray).draw();
    }

  }


  InitMainTableQtyPO();
  InitMainTableUnitCost();
  // InitMainTableComment();
  UpdateTotals('PO');
}


function InitMainTableQtyPO() {

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

function initBrowseTable(inputValue) {
  if (inputValue.length >= 3) {
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
      .then(function () {
        InitTableUnitCost();
      })
      .catch(function (error) {
        console.error("Error:", error);
      });
  }
}