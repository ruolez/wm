const PopoverManager = (function() {
  let instance;

  function createInstance() {
    let isPopoverActive = false;
    let onPopoverCloseCallback = null; // Переменная для хранения колбэка

    function showPopover(element, row, unitprice, classlist,maintable = false) {
      // Проверка, активен ли уже popover
      if (isPopoverActive) return;

      isPopoverActive = true;

      const form = document.getElementById("exampleModal");
      form.classList.add("disable-clicks");

      let overlay = document.createElement('div');
      overlay.classList.add('form-overlay');
      form.appendChild(overlay);

      $(element).popover('dispose');
      $(element).popover({
        html: true,
        id: 'popvb',
        content: function() {
          return `<div class="popover-body p-0 text-center">
                    <a href="#" class="btn btn-secondary btn-sm" id="YesRemember">Yes</a>
                    <a href="#" class="btn btn-secondary btn-sm" id="NoRemember">No</a>
                  </div>`;
        },
        title: `<div p-0 text-center>Remember price?</div>`,
        placement: 'top',
        trigger: 'manual'
      }).popover('show');

      // Восстановление состояния документа и popover
      const restoreDocumentState = () => {
        form.classList.remove("disable-clicks");
        overlay.remove();
        $(element).popover('dispose');
        isPopoverActive = false;
        $(document).off("click", "#YesRemember");
        $(document).off("click", "#NoRemember");
        $(document).off("keydown", handleKeyPress);
        element.focus();

        // Если установлен колбэк, вызываем его после закрытия popover
        if (onPopoverCloseCallback) {
          onPopoverCloseCallback();
        }
      };

      // Обработка кликов по "Yes" и "No"
      $(document).on("click", "#YesRemember", () => {
        row.data().rememberprice = 1;
        if (unitprice) {
          classlist.remove('unsetbackground');
          unitprice.childNodes[0].style.backgroundColor = 'var(--tblr-highlight-bg)';
        }
        if (maintable){
          UpdateMainTableItems(null, row, null);
        }else{
          UpdateItems(null, row, null);
        }

        restoreDocumentState();
      });

      $(document).on("click", "#NoRemember", () => {
        row.data().rememberprice = 0;
        if (unitprice) {
          unitprice.childNodes[0].style.backgroundColor = '';
          classlist.add('unsetbackground');
          classlist.add('black-text-color');
        }
        if (maintable){
          UpdateMainTableItems(null, row, null);
        }else{
          UpdateItems(null, row, null);
        }
        restoreDocumentState();
      });

      // Обработка нажатий на клавиши 'y' и 'n'
      const handleKeyPress = (event) => {
        event.preventDefault();
        if (event.key === "y") {
          $("#YesRemember").trigger("click");
        } else if (event.key === "n") {
          $("#NoRemember").trigger("click");
        }
      };

      $(document).on("keydown", handleKeyPress);
    }

    return {
      showPopover: showPopover,
      isPopoverActive: function() {
        return isPopoverActive;
      },
      // Добавление возможности установить callback на закрытие popover
      setOnPopoverClose: function(callback) {
        onPopoverCloseCallback = callback;
      }
    };
  }

  return {
    getInstance: function() {
      if (!instance) {
        instance = createInstance();
      }
      return instance;
    }
  };
})();



let isTabBlocked = false;
let isChanged = false;
function Changed(){
  isChanged = true;
  let $changedLabel = $('#changedLabel');
  if ($changedLabel.length > 0) {
    $changedLabel.show(); // Показываем элемент
  }
  SetDBDropDown(true);
}

function IsChanged(){
  return isChanged;
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

function Debounce(func, delay) {
  let timerId;
  return function (...args) {
    clearTimeout(timerId);
    timerId = setTimeout(() => {
      func.apply(this, args);
    }, delay);
  };
}

function ReplaceSpace(inputValue) {
  return inputValue.replace(/ /g, "%");
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

function SetupRowClickHandler(tableId) {
  $(`#${tableId}`).on("click", "tbody tr", function (event) {
    var isSelected = $(this).hasClass("selected");

    $(`#${tableId} .btn-danger`).removeClass("btn-danger").addClass("btn-outline-danger");
    $(`#${tableId} .btn-warning`).removeClass("btn-warning").addClass("btn-outline-warning");
    $(`#${tableId} .btn-info`).removeClass("btn-info").addClass("btn-outline-info");
    $(`#${tableId} .btn-success`).removeClass("btn-success").addClass("btn-outline-success");
    $(`#${tableId} .btn-secondary`).removeClass("btn-secondary").addClass("btn-outline-secondary");

    if (!isSelected) {
      $(this).find(".btn-outline-danger").removeClass("btn-outline-danger").addClass("btn-danger");
      $(this).find(".btn-outline-warning").removeClass("btn-outline-warning").addClass("btn-warning");
      $(this).find(".btn-outline-info").removeClass("btn-outline-info").addClass("btn-info");
      $(this).find(".btn-outline-success").removeClass("btn-outline-success").addClass("btn-success");
      $(this).find(".btn-outline-secondary").removeClass("btn-outline-secondary").addClass("btn-secondary");
    }
  });
}

function generateData() {
  return {
    data: [],
  };
}

function AssignBusnessAcc(id, arr) {
  var foundItem = arr.data.find(function (item) {
    return item.id == id;
  });
  $("#bnameInput").attr("data-id", foundItem.id);
  $("#acnumInput").attr("data-id", foundItem.id);
  $("#acnumInput").val(foundItem.anum);
}

function AssignAccNum(id, arr) {
  var foundItem = arr.data.find(function (item) {
    return item.id == id;
  });
  $("#acnumInput").attr("data-id", foundItem.id);
  $("#bnameInput").val(foundItem.bname);
  $("#bnameInput").attr("data-id", foundItem.id);
}

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

function GetColNumber(tablename, colname) {
  let table = document.getElementById(tablename);
  let headerRow = table.rows[0];
  let totalIndex = Array.from(headerRow.cells).findIndex(
    (cell) => cell.textContent.trim().toLowerCase() === colname.toLowerCase()
  );
  return totalIndex;
}

function IsGroupItems() {
  return $('#groupitems')?.prop('checked') ?? false;
}

function AddAdditionalColumns(items, qty = 0) {
  items.data.forEach(function (item) {

    item.Qty = qty;
    item.Total = item.Qty * item.UnitPrice;
    item.TotalCost = item.Qty * item.UnitCost;
    item.Comment = "";
    item.S = false;

    if (item?.UnitCost != 0) {

      item.ProfitMargin = ((item.UnitPrice / item.UnitCost) - 1)*100;
  } else {

      item.ProfitMargin = 0;
  }



  });
  return items;
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

function SetTodayDate(selector) {
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

  $(selector)?.val(formattedDate);
}



function UpdateTableValues() {
  let table = $("#browse-items-table").DataTable();

  // Iterate over each item in mainitemstable
  mainitemstable?.forEach(function (qitem) {
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
      tableItem.UnitCost = qitem.UnitCost;
      tableItem.Total = qitem.Total;
      tableItem.TotalCost = qitem.TotalCost;
      tableItem.S = qitem.Qty > 0;
      tableItem.rememberprice = qitem.rememberprice;
      // Invalidate the row to reflect the changes
      table.row(rowIndex[0]).invalidate();
    }
  });

  // Redraw the entire table after updating all matching items
  table.draw(false);
}

function UpdateTotals (obj="quotation") {
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

  let totalCostColumnIndex = obj === 'PO' ? 9 : 10;

  let totalCost = table
    .column(totalCostColumnIndex)
    .data()
    .reduce(function (acc, val) {
      return acc + parseFloat(val);
    }, 0);


    let totalProfitMargin = 0;
    if (totalCost > 0) {
      totalProfitMargin = ((totalPrice / totalCost) - 1)*100; // Replace with your formula
    }

  $("#totalitems").find("strong").eq(0).text(totalItems);
  $("#totalqty").find("strong").eq(0).text(totalQuantity);
  $("#totalcost").find("strong").eq(0).text(totalCost.toFixed(2));
  $("#totalprice").find("strong").eq(0).text(totalPrice.toFixed(2));
  $("#totalprofitmargin").find("strong").eq(0).text(totalProfitMargin.toFixed(2) + "%");
}

function UpdateItems(updatedCell, updatedRow, oldValue) {
  let updatedSKU = updatedRow.data().SKU;
  let updatedQty = updatedRow.data().Qty;
  let updatedUnitPrice = updatedRow.data().UnitPrice;
  let updatedUnitCost = updatedRow.data().UnitCost;
  let rememberPrice = updatedRow.data().rememberprice||0;

  let updatedTotal = (updatedQty * updatedUnitPrice).toFixed(2);
  let updatedTotalCost = (updatedQty * updatedUnitCost).toFixed(2);



  updatedRow.data().Total = updatedTotal;
  updatedRow.data().TotalCost = updatedTotalCost;

  updatedRow.data().S = updatedRow.data().Qty > 0 ? true : false;
  updatedRow.data().UnitPrice = updatedRow.data()?.UnitPrice;

  UpdateSelectedPrewiew(updatedRow, selectboxColNum, updatedRow.data().S);
  UpdateTotalPrewiew(updatedRow, totalColNum, updatedTotal);
  UpdateTotalPrewiew(updatedRow, totaCostColNum, updatedTotalCost);
  UpdateQtyPrewiew(updatedRow, qtyColNum, updatedQty);

  if (updatedQty == 0) {
    mainitemstable = mainitemstable.filter(function (item) {
      updatedRow.data().Total = 0;
      return item.SKU !== updatedSKU;
    });
  } else {
    let isNeedsUpdated = true;
    mainitemstable = mainitemstable.map(function (item) {


      if (item.SKU === updatedSKU) {
        isNeedsUpdated = false;
        return { ...item, Qty: updatedQty, UnitPrice: updatedUnitPrice, UnitCost: updatedUnitCost, Total: updatedTotal, TotalCost: updatedTotalCost ,rememberprice:rememberPrice};
      }
      return item;


    });

    if (isNeedsUpdated) {
      mainitemstable.push(updatedRow.data());
    }
  }
}

function UpdateMainTableItems(updatedCell, updatedRow, oldValue) {

  let updatedQty = updatedRow.data().Qty;
  let updatedUnitPrice = updatedRow.data().UnitPrice;
  let updatedUnitCost = updatedRow.data().UnitCost;
  let updatedProfitMargin = updatedRow?.data()?.ProfitMargin?.toFixed(2)+'%';


  let updatedTotal = (updatedQty * updatedUnitPrice).toFixed(2);
  let updatedTotalCost = (updatedQty * updatedUnitCost).toFixed(2);

  updatedRow.data().Total = updatedTotal;
  updatedRow.data().TotalCost = updatedTotalCost;

  updatedRow.data().S = updatedRow.data().Qty > 0 ? true : false;

  UpdateTotalPrewiew(updatedRow, MaintotalColNum, updatedTotal);
  UpdateTotalPrewiew(updatedRow, MaintotalCostColNum, updatedTotalCost);
  if (ProfitMarginColNum){
    UpdateTotalPrewiew(updatedRow, ProfitMarginColNum, updatedProfitMargin);
    UpdateTotals();
  }
  else{
    UpdateTotals('PO');
  }



}

function UpdateTotalPrewiew(updatedRow, totalColNum, updatedTotal) {

  let row = updatedRow.node().getElementsByTagName("td")[totalColNum];
  if (row) {
    row.textContent =
      updatedTotal;
  }



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

function CopyItemsFromMainTable(selector) {

  if (IsGroupItems()) {
    mainitemstable = [];
    itemsTable = $(selector).DataTable().rows().data().toArray();

    mainitemstable = itemsTable.reduce((acc, item) => {

      const existingItemIndex = acc.findIndex(existingItem => existingItem.SKU === item.SKU);
      if (existingItemIndex !== -1) {

        acc[existingItemIndex] = item;
      } else {

        acc.push(item);
      }
      return acc;
    }, []);
  }
  else {
    mainitemstable = [];
  }
}

async function MoveToMainTable(object = 'addItemButton') {
  var table = $("#items-table").DataTable();

  if (IsGroupItems()) {

    var updatedData = [];
    var newData = [];

    mainitemstable.forEach(item => {

      const existingIndex = table.rows().indexes().toArray().reverse().find(index => {
        const rowData = table.row(index).data();
        return rowData && rowData.SKU === item.SKU;
      });

      if (existingIndex !== undefined) {

        updatedData.push({ index: existingIndex, data: item });
      } else {

        newData.push(item);
      }
    });


    if (updatedData.length > 0) {
      var allData = table.data().toArray();
      updatedData.forEach(update => {
        allData[update.index] = update.data;
      });
      table.clear().rows.add(allData).draw();
    }

    if (newData.length > 0) {
      table.rows.add(newData).draw();
    }
  } else {
    let currentData = table.data().toArray();
    let combinedData = currentData.concat(mainitemstable);
    table.clear().rows.add(combinedData).draw();


  }

  $("#exampleModal").modal("hide");

  if (object == 'addItemButton') {
    await UpdateStock();
    InitMainTableQty();
    InitMainTableUnitPrice();
    InitMainTableComment();
    UpdateTotals();
  } else if (object == 'addItemButtonPO') {
    InitMainTableQtyPO();
    InitMainTableUnitCost();
    UpdateTotals('PO');
  }

  if (table.data().length > 0) {
    $('#items-table').parent().removeClass('invalid-input');
  }

  SetDBDropDown(CheckDBBlock());
  Changed();
  ///

}


function InitCheckboxes() {
  // Get all the checkboxes in the first column
  const checkboxes = document.querySelectorAll(
    '#browse-items-table tbody tr td:first-child input[type="checkbox"]'
  );

  // Loop through each checkbox and attach a change event listener
  checkboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", function () {
      let table = $("#browse-items-table").DataTable();

      let closestRow = $(this).closest("tr");
      let row = table.row(closestRow);
      row.data().Qty = this.checked ? 1 : 0;
      UpdateItems(null, row, null);
    });
  });
}

function initDecription() {

  const cells = document.querySelectorAll('#browse-items-table tbody tr td:nth-child(3)');

  cells.forEach((cell) => {
    cell.addEventListener("click", function () {
      let table = $("#browse-items-table").DataTable();

      let closestRow = $(this).closest("tr");
      let row = table.row(closestRow);
      if (row.data().Qty === undefined || row.data().Qty === null) {
        row.data().Qty = 1;
      } else {
        // If Qty is not undefined or null, toggle its value
        if (row.data().Qty == 0){
          row.data().Qty=1;
        }
       // row.data().Qty = row.data().Qty === 0 ? 1 : 0;
      }
      UpdateItems(null, row, null);


    });
  });

}

$("#exampleModal").on("hidden.bs.modal", function () {
  CleanSearch("#modalsearch");
  CleanDatable("#browse-items-table");
});

function InitQty() {
  const numberInputs = document.querySelectorAll(
    '#browse-items-table tbody tr td:nth-child(2) input[type="number"]'
  );

  // Loop through each input and attach event listeners
  numberInputs.forEach((num) => {
    num.addEventListener("click", function () {
      // Select all the content of the input field
      this.select();
    });

    num.addEventListener("change", function () {
      let newValue = parseFloat(this.value);


      if (isNaN(newValue) || newValue < 0) {

        let table = $("#browse-items-table").DataTable();
        let closestRow = $(this).closest("tr");
        let row = table.row(closestRow);
        this.value = row.data().Qty;
        return;
      }


      let table = $("#browse-items-table").DataTable();
      let closestRow = $(this).closest("tr");
      let row = table.row(closestRow);
      row.data().Qty = newValue;
      UpdateItems(null, row, null);
    });



    num.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        // Prevent default behavior of Enter key
        e.preventDefault();
        e.stopPropagation();
        // Move focus to the element with id 'hhh'
        let searchField = document.getElementById("modalsearch");
searchField.focus();

// Place the cursor at the end of the text
let valueLength = searchField.value.length;
searchField.setSelectionRange(valueLength, valueLength);
      }

      if (e.key === ' ') {
        e.preventDefault();
        e.stopPropagation();
        let table = $("#browse-items-table").DataTable();

        let closestRow = $(this).closest("tr");
        let row = table.row(closestRow);
        if (row.data().Qty === undefined || row.data().Qty === null) {
          row.data().Qty = 1;
        } else {
          // If Qty is not undefined or null, toggle its value
         // row.data().Qty = row.data().Qty === 0 ? 1 : 0;
        }
        UpdateItems(null, row, null);

      }

    });
  });
}

function InitUnitPrice() {
  const numberInputs = document.querySelectorAll(
    '#browse-items-table tbody tr td:nth-child(4) input[type="number"]'
  );
  const popoverManager = PopoverManager.getInstance();

  numberInputs.forEach((num) => {
    num.addEventListener("change", function () {
      let table = $("#browse-items-table").DataTable();
      let closestRow = $(this).closest("tr");
      let row = table.row(closestRow);
      this.value = parseFloat(this.value).toFixed(2);
      row.data().UnitPrice = this.value;

      if (row.data().Qty <= 0) {
        row.data().S = true;
        row.data().Qty = 1;
      }

      let unitprice = closestRow[0].querySelector('.unitprice');
      let classlist = this.classList;

      // Блокируем табуляцию
      isTabBlocked = true;

      // Вызываем popover через менеджер
      this.blur();
      popoverManager.showPopover(this, row, unitprice, classlist);

      // Разблокируем табуляцию при закрытии поповера
      popoverManager.setOnPopoverClose(() => {
        isTabBlocked = false;
      });
    });
  });
}

///init main table
function InitMainTableQty() {
  const numberInputs = $('#items-table tbody tr td:nth-child(1) input[type="number"]');

  numberInputs.each(function () {
    $(this).on("click", function () {
      // Select all the content of the input field
      this.select();
    });

    $(this).on("change", function () {
      let table = $("#items-table").DataTable();
      let closestRow = $(this).closest("tr");
      let row = table.row(closestRow);
      row.data().Qty = this.value;
      UpdateMainTableItems(null, row, null);
    });

    $(this).on("keydown", function (e) {
      if (e.key === "Enter") {
        // Prevent default behavior of Enter key
        e.preventDefault();
        // Move focus to the element with id 'hhh'
        $('#quicksearch').focus();
      }
    });
  });
}

function InitMainTableUnitPrice() {
  const numberInputs = document.querySelectorAll(
    '#items-table tbody tr td:nth-child(3) input[type="number"]'
  );
  const popoverManager = PopoverManager.getInstance(); // Менеджер поповеров

  numberInputs.forEach((num) => {
    num.addEventListener("change", function () {
      let table = $("#items-table").DataTable();
      let closestRow = $(this).closest("tr");
      let row = table.row(closestRow);
      this.value = parseFloat(this.value).toFixed(2);
      row.data().UnitPrice = this.value;

      if (row.data().UnitCost != 0) {
        row.data().ProfitMargin = ((row.data().UnitPrice / row.data().UnitCost) - 1) * 100;
      } else {
        row.data().ProfitMargin = 0; // Если UnitCost равен 0
      }

      let unitprice = closestRow[0].querySelector('.unitprice');
      let classlist = this.classList;

      // Блокируем табуляцию
      isTabBlocked = true;

      // Убираем фокус с инпута, чтобы показать поповер
      this.blur();

      // Вызов поповера через менеджер
      popoverManager.showPopover(this, row, unitprice, classlist,true);

      // Разблокировка табуляции при закрытии поповера
      popoverManager.setOnPopoverClose(() => {
        isTabBlocked = false;
      });

      UpdateMainTableItems(null, row, null); // Обновление данных в таблице
    });
  });
}

function InitMainTableComment() {
  const textInputs = document.querySelectorAll(
    '#items-table tbody tr td:nth-child(8) input[type="text"]'
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

function CleanSearch(searchid) {
  $(searchid).val("");
}

$(document).on("keydown", function (e) {
  if (e.key === "Delete") {

    if ($(document.activeElement).is("input")) {
      return;
    }
    removeRow();
    UpdateTotals();
  }
});

function removerow(event, obj) {

  event.preventDefault();
  var table = $('#items-table').DataTable();
  var row = $(event.target).closest('tr');
  table.row(row).remove().draw(false);
  if (table.data().toArray().length <= 0) {
    $('#quicksearch')?.focus();
  }
  UpdateTotals(obj);
  SetDBDropDown(CheckDBBlock());
  Changed();
}

function removeRow() {
  var table = $("#items-table").DataTable();
  var selectedRows = table.rows({ selected: true }).indexes();
  selectedRows.each(function (index) {
    table.row($(this)).remove().draw(false);
  });
  if (table.data().toArray().length <= 0) {
    $('#quicksearch')?.focus();
  }
  else {
    $(document.activeElement).blur();
  }
  SetDBDropDown(CheckDBBlock());
  Changed();
}

function AddQuickSearchItem(items) {


  if (items?.data?.length > 0) {
    let table = AddAdditionalColumns(items, (qty = 1));
    MoveQuickSearch(table?.data[0]);
    $('#items-table').parent().removeClass('invalid-input');

  }
  Changed();
}

function MoveQuickSearch(item) {
  let table = $("#items-table").DataTable();

  function AddQuickSearchItem(items) {


    if (items?.data?.length > 0) {
      let table = AddAdditionalColumns(items, (qty = 1));
      MoveQuickSearch(table?.data[0]);
      $('#items-table').parent().removeClass('invalid-input');

    }

  }

  function MoveQuickSearch(item) {
    ;
    let table = $("#items-table").DataTable();


    if (!IsGroupItems()) {

      let itemsArray = [item];
      table.rows.add(itemsArray).draw();
    }
    else {
      let items = table.rows().data().toArray();

      let lastItem = items.findLast(element => element.SKU === item.SKU);

      if (lastItem) {

        lastItem.Qty = Number(lastItem.Qty) + 1;
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


    InitMainTableQty();
    InitMainTableUnitPrice();
    InitMainTableComment();
    UpdateTotals();
    Changed();
  }
  if (!IsGroupItems()) {

    let itemsArray = [item];
    table.rows.add(itemsArray).draw();

  }
  else {
    let items = table.rows().data().toArray();

    let lastItem = items.findLast(element => element.SKU === item.SKU);

    if (lastItem) {
      lastItem.Qty = Number(lastItem.Qty) + 1;
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

  // let lastRowIndex = table.rows().count() - 1;
  // table.row(lastRowIndex||0).select();


  InitMainTableQty();
  InitMainTableUnitPrice();
  InitMainTableComment();
  UpdateTotals();
  Changed();



  document.getElementById('items-table').scrollIntoView({ behavior: 'smooth', block: 'end' })

}

function QuickSearch() {
  return GetQuickSearchItem();
}

function SetDBDropDown(state = true) {
  $('#dropdownMenuButton')?.attr('disabled', state);
}




function CheckDBBlock() {

  let tableLength = $('#items-table').DataTable().data().toArray().length;
  let bname = $('#bnameInput').val();
  let acnum = $('#acnumInput').val();

  let qnumber = $('#qnumber').val();
  let ponumber = $('#POID').val();


  if (qnumber || ponumber) {
    return true;
  }


  if (tableLength > 0 || (bname && acnum)) {
    return true;
  } else {
    return false;
  }

}

$(document).keydown(function (event) {

  if (event.keyCode === 27) {
    // The Esc key was pressed
    CleanSearch("#modalsearch");
    CleanDatable("#browse-items-table");
    $("#exampleModal").modal("hide");
    $("#massUpdateModal").modal("hide");

    // Add your logic here
  }


  ///disable enter in inputs
  if (event.keyCode === 13 && ($(document.activeElement).attr("id") !== "quicksearch" || typeof $(document.activeElement).attr("id") === 'undefined')) {
    event.preventDefault();
    $(document.activeElement).blur();
    return false;
  }


  if (event.which === 113) { // F2
    ChangeQuickSearchParametr();
  }

  if (event.which === 114 && ($('#browseItemsButton').css('pointer-events') !== 'none')) { // F3
    CopyItemsFromMainTable("#items-table");
    $('#exampleModal').modal('show');
    SetlookinDropdown();

  }

});

$('#exampleModal').on('shown.bs.modal', function () {
  BrowseItems();
  $('#modalsearch').focus();

});

function Tabulation(element, e) {
  // Блокировка табуляции, если активен поповер
  if (isTabBlocked) return;

  var focusableElements = $(element).find('input:visible, button:visible, select:visible, textarea:visible, [tabindex]:visible')
    .not('input.form-check-input .btn-close, thead *')
    .not('.btn-close')
    .not('.form-check-input')
    .not('.btn')
    .filter('.focusable');

  var currentIndex = focusableElements.index(document.activeElement);

  var currentElement = focusableElements.eq(currentIndex);
  var columnClass = currentElement.hasClass('columnOne') ? 'columnOne' : currentElement.hasClass('columnTwo') ? 'columnTwo' : 'columnOne';

  if ((e.key === 'ArrowDown' || e.keyCode === 40 || e.key === 'Tab') && !e.shiftKey) {
    e.preventDefault();

    if (currentIndex === -1) {
      var firstElement = focusableElements.filter('.columnOne').first();
      if (firstElement.length) {
        $('.selected').removeClass('selected');
        firstElement.parent().parent().addClass('selected');
        firstElement.focus().select();
      }
      return;
    }

    if (currentIndex + 1 < focusableElements.length) {
      var nextElement = focusableElements.eq(currentIndex + 1);
      var nextIndex = currentIndex + 1;
      while (nextIndex < focusableElements.length && !focusableElements.eq(nextIndex).hasClass(columnClass)) {
        nextIndex++;
      }
      if (nextIndex < focusableElements.length) {

        const popoverManager = PopoverManager.getInstance();
        if (!popoverManager.isPopoverActive()) {
          $('.selected').removeClass('selected');
         let checkel =  focusableElements.eq(nextIndex).focus();
          if (popoverManager.isPopoverActive()){
            focusableElements.eq(currentIndex).focus();
            focusableElements.eq(currentIndex).select();
            focusableElements.eq(currentIndex).parent().parent().addClass('selected');
          }
          else{
            checkel.select();
            focusableElements.eq(nextIndex).parent().parent().addClass('selected');
          }



        } else {
          // Do nothing if popover is active
        }
      }
    }
  } else if (e.key === 'ArrowUp' || e.keyCode === 38 || (e.key === 'Tab' && e.shiftKey)) {
    e.preventDefault();
    var prevIndex = currentIndex - 1;
    while (prevIndex >= 0 && !focusableElements.eq(prevIndex).hasClass(columnClass)) {
      prevIndex--;
    }
    if (prevIndex >= 0) {
      $('.selected').removeClass('selected');
      focusableElements.eq(prevIndex).parent().parent().addClass('selected');
      focusableElements.eq(prevIndex).focus().select();
    }
  } else if (e.key === 'ArrowRight' || e.keyCode === 39) {
    e.preventDefault();
    if (columnClass === 'columnOne') {
      var nextElement = focusableElements.eq(currentIndex + 1);
      while (nextElement.length && !nextElement.hasClass('columnTwo')) {
        currentIndex++;
        nextElement = focusableElements.eq(currentIndex + 1);
      }
      if (nextElement.length) {
        nextElement.focus().select();
      }
    }
  } else if (e.key === 'ArrowLeft' || e.keyCode === 37) {
    e.preventDefault();
    if (columnClass === 'columnTwo') {
      var prevElement = focusableElements.eq(currentIndex - 1);
      while (prevElement.length && !prevElement.hasClass('columnOne')) {
        currentIndex--;
        prevElement = focusableElements.eq(currentIndex - 1);
      }
      if (prevElement.length) {
        prevElement.focus().select();
      }
    }
  }

  lastFocusedElement = document.activeElement;
}





$('#items-table').on('keydown', function (e) {
  if (e.key === 'Tab' || e.keyCode === 9) {
    var focusableElements = $(this).find('input:visible').not('.btn-close, thead *').not('.btn-close').not('.form-check-input').not('.width100');
    var currentIndex = focusableElements.index(document.activeElement);

    if (!e.shiftKey && (currentIndex === focusableElements.length - 1)) {
      e.preventDefault();
      $(this).find('input[type="number"]').first().focus();
    }
  }
});

//modal search select value on click
$('#modalsearch').on('click', function () {
  if ($(this).val()) {
    $(this).select();
  }
});
$(document).ready(function () {
  $('#modalsearch').on('keydown', function (e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      e.stopPropagation();
      // browse-items-table_wrapper
      if (!lastFocusedElement) {
        $('#browse-items-table_wrapper').find('input, button, select, textarea, [tabindex]')
          .not('.btn-close, thead *')
          .not('.btn')
          .not('.form-check-input')
          .filter('.focusable')
          .first()
          .focus()
          .select();
      }
      else {

        lastFocusedElement?.focus();
      }

    }
  });
});

$(document).ready(function () {
  $("#lookinDropdown")
    .next(".dropdown-menu")
    .on("click", ".dropdown-item", function () {
      let inputValue = document.getElementById("modalsearch").value;
      if (model.label != 'Mass Update') {
        initBrowseTable(inputValue);
      }
      SetlookinDropdown();
    });
});

///search
document.getElementById("modalsearch")?.addEventListener("input", Debounce(function (event) {
  let inputValue = event.target.value;
  if (model.label != 'Mass Update') {
    initBrowseTable(inputValue);
  }
}, 500));



///modal when opened
$(document).on("click", "#browseItemsButton", function () {
  ///add if checked
  CopyItemsFromMainTable("#items-table");
  lastFocusedElement = null;
});

$("#exampleModal").on("hidden.bs.modal", function () {
  lastFocusedElement = null;
  CleanSearch("#modalsearch");
  CleanDatable("#browse-items-table");
});

$("#addItemButton").click(function (selector) {
  MoveToMainTable(selector.target.id);
});

$("#addItemButtonPO").click(function (selector) {
  MoveToMainTable(selector.target.id);
});


///modal when opened
$(document).on("click", "#browseItemsButton", function () {
  ///add if checked
  CopyItemsFromMainTable("#items-table");

});

function DisableSearch() {
  document.getElementById("searchPanel").style.opacity = 0.5;
  document.getElementById("searchPanel").style.pointerEvents = 'none';
}

function EnableSearch() {
  document.getElementById("searchPanel").style.opacity = 1;
  document.getElementById("searchPanel").style.pointerEvents = 'all';
}

function SetDb(value) {
  setCookie('DB', value, days = 365)
}

function GetDb() {
  return getCookie('DB');
}

function SetlookinDropdown() {
  setCookie('lookinDropdown', GetDropdownValue("#lookinDropdown").searchById, days = 365)
}

function GetlookinDropdown() {
  return getCookie('lookinDropdown');
}

function SetTableLenght(lenght = 10) {

  setCookie('pageLength', lenght, days = 365)
}

function GetTableLenght() {
  return getCookie('lookinDropdown');
}


function setCookie(name, value, days = 365) {
  let expires = "";
  if (days) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    expires = "; expires=" + date.toUTCString();
  }
  document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

function getCookie(name) {
  const nameEQ = name + "=";
  const ca = document.cookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
  }
  return null;
}

function setDropdownFromCookie() {
  const dropdownValue = getCookie('lookinDropdown');
  if (dropdownValue) {


    const numericValue = parseInt(dropdownValue, 10);  // Преобразование строки в число
    if (!isNaN(numericValue)) {
      let $dropdownButton = $('#lookinDropdown');
      let $dropdownMenu = $('#lookinDropdownmenu');
      let $dropdownItem = $dropdownMenu.find("[data-value='" + numericValue + "']");

      if ($dropdownItem.length > 0) {
        $dropdownButton.attr('data-value', numericValue);
        $dropdownButton.text($dropdownItem.text());
      }
    }

  }
}


$('#exampleModal').on('show.bs.modal', function () {
  setDropdownFromCookie()
});

$(document).ready(function () {

  SetupRowClickHandler("example");

});


$('#exampleModal').on('keydown', function (e) {

  if (e.target.id !='modalsearch'){
    Tabulation(this, e);
  }


  if ((e.key === 'Escape' || e.keyCode === 27 || e.keyCode === 114) && $("#browse-items-table").DataTable().data().length <= 0) {
    lastFocusedElement = null;
    $('#exampleModal').modal('hide');
  }

  if ((e.ctrlKey || e.metaKey || e.altKey) && (e.key === 'k' || e.keyCode === 75)) {
    $('#modalsearch').focus();
    MoveToMainTable();
  }
});

$('#tablezone').on('keydown', function (e) {
  lastFocusedElement = null;
  Tabulation(this, e);
});



function AddKeyUpDownListeners(tableId) {
  document.addEventListener('keydown', (event) => keyNavigationHandler(event, tableId));
}

function RemoveKeyUpDownListeners(tableId) {
  document.removeEventListener('keydown', (event) => keyNavigationHandler(event, tableId));
}

function keyNavigationHandler(event, tableId) {
  const table = $(`#${tableId}`).DataTable();
  const selectedRow = table.row('.selected');

  // Если строка выбрана
  if (selectedRow.any()) {
    const index = selectedRow.index();
    const rowCount = table.rows({ filter: 'applied' }).count(); // Получаем количество строк с учетом фильтра

    let newRow; // Новая строка, которую будем выбирать

    // Определяем, является ли текущая строка крайней
    const isLastRow = index === rowCount - 1; // Проверяем, является ли последней строкой
    const isFirstRow = index === 0; // Проверяем, является ли первой строкой

    // Сначала возвращаем классы в предыдущей строке к начальному состоянию, если это не крайняя строка
    const previousRowNode = selectedRow.node();
    if (previousRowNode && !(isFirstRow && event.key === 'ArrowUp') && !(isLastRow && event.key === 'ArrowDown')) {
      $(previousRowNode).find(".btn-danger").removeClass("btn-danger").addClass("btn-outline-danger");
      $(previousRowNode).find(".btn-warning").removeClass("btn-warning").addClass("btn-outline-warning");
      $(previousRowNode).find(".btn-info").removeClass("btn-info").addClass("btn-outline-info");
      $(previousRowNode).find(".btn-success").removeClass("btn-success").addClass("btn-outline-success");
      $(previousRowNode).find(".btn-secondary").removeClass("btn-secondary").addClass("btn-outline-secondary");
    }

    if (event.key === 'ArrowDown' && index < rowCount - 1) {
      selectedRow.deselect();
      newRow = table.row(index + 1).select();
    } else if (event.key === 'ArrowUp' && index > 0) {
      selectedRow.deselect();
      newRow = table.row(index - 1).select();
    }

    // Если строка выбрана, прокручиваем таблицу к ней
    if (newRow) {
      const rowNode = newRow.node();
      rowNode.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

      // Меняем классы кнопок в новой строке
      $(rowNode).find(".btn-outline-danger").removeClass("btn-outline-danger").addClass("btn-danger");
      $(rowNode).find(".btn-outline-warning").removeClass("btn-outline-warning").addClass("btn-warning");
      $(rowNode).find(".btn-outline-info").removeClass("btn-outline-info").addClass("btn-info");
      $(rowNode).find(".btn-outline-success").removeClass("btn-outline-success").addClass("btn-success");
      $(rowNode).find(".btn-outline-secondary").removeClass("btn-outline-secondary").addClass("btn-secondary");
    }
  } else {
    // Если строка не выбрана, выберем первую строку при нажатии стрелки вниз
    if (event.key === 'ArrowDown') {
      newRow = table.row(0).select(); // Выбираем первую строку
      const rowNode = newRow.node();
      rowNode.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

      // Меняем классы кнопок в первой строке
      $(rowNode).find(".btn-outline-danger").removeClass("btn-outline-danger").addClass("btn-danger");
      $(rowNode).find(".btn-outline-warning").removeClass("btn-outline-warning").addClass("btn-warning");
      $(rowNode).find(".btn-outline-info").removeClass("btn-outline-info").addClass("btn-info");
      $(rowNode).find(".btn-outline-success").removeClass("btn-outline-success").addClass("btn-success");
      $(rowNode).find(".btn-outline-secondary").removeClass("btn-outline-secondary").addClass("btn-secondary");
    }
  }
}




