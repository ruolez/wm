async function GetPO() {
  try {
    let queryParams = new URLSearchParams(window.location.search);
    var paramsObject = {};

    for (var pair of queryParams.entries()) {
      paramsObject[pair[0]] = pair[1];
    }


    if ((Object.values(paramsObject).length > 0)) {
      let data = await RequestPO(paramsObject);
      isCommitAllowed = data?.isCommitAllowed === 1 ? true : false;
      PopulatePODetails(data);

    }
  } catch (error) {
    toastr.error(error.text);
  }
}

async function RequestPO(paramsObject) {
  try {
    const response = await $.ajax({
      url: model.apiUrl + "/getpo",
      type: "POST",
      data: paramsObject,
      traditional: true,
      dataType: "json",
    });
    return response;
  } catch (error) {
    throw error;
  }
}

async function GetBusneessInfo(inputValue, name) {
  return new Promise((resolve, reject) => {
    let searchData = {
      DB: GetDb(),
      searchBy: name,
      searchValue: inputValue,
    };

    $.ajax({
      url: model.apiUrl + "/getsupplier",
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

function ShowPoStatus(status) {
  $("#POstatus").text(status);
  $('#POstatus').removeClass('display-none');
}

function PopulatePODetails(data) {
  $('#ponumber').val(data.PONumber);
  $('#POid').val(data?.POid ?? 0);

  // $('#InvoiceNumber').val(data?.InvoiceNumber??'');
  // if ($('#InvoiceNumber').val()){
  //   ShowInvoiceLabel($('#InvoiceNumber').val());
  // }


  let formattedDate = new Date(data.Date).toISOString().split('T')[0];

  $('#podate').val(formattedDate);
  $('#status').val(data.Status);
  if (data.Status == 1) {
    ShowPoStatus('Commited');
  }
  else {
    ShowPoStatus('Placed');
  }


  $('#POID').val(data.POid);

  $("#bnameInput").val(data.bnum);
  $("#bnameInput").attr("data-id", data.anum);

  $("#acnumInput").val(data.anum);
  $("#acnumInput").attr("data-id", data.bnum);

  $("#contactname").val(data.contactname);
  $("#phone").val(data.Phone_Number);
  $("#notes").val(data.Notes);


  var tableData = [];

  data.data_getpo.forEach(function (item) {
    let newItem = Object.assign({}, item);
    if (!newItem.hasOwnProperty('Description')) {
      newItem.Description = "";
    }
    else {
      newItem.Description = item.Description;
    }
    if (!newItem.hasOwnProperty('UnitPrice')) {
      newItem.UnitPrice = item.UnitCost;
    }
    if (!newItem.hasOwnProperty('Stock')) {
      newItem.Stock = 0;
    }
    if (!newItem.hasOwnProperty('TotalCost')) {
      newItem.TotalCost = newItem.QTY * newItem.UnitCost;
    }
    if (newItem.hasOwnProperty('QTY')) {
      newItem.Qty = newItem.QTY;
      delete newItem.QTY;
    }
    tableData.push(newItem);
  });

  let table = $("#items-table").DataTable();

  table.rows.add(tableData).draw();

  InitMainTableQty();
  InitMainTableUnitCost();
  UpdateTotals('PO');
  ChangeToEditFields();




}

async function SavePO() {
  if (!ValidateForm()) {

    return false;
  }

  let header = PrepareMainFields();
  let details = PrepareItemsTable();
  let poData = {
    ...header,
    items: JSON.stringify(details)

  };

  try {

    const response = await SubmitPO(poData);
    if (response?.data_create_po[0]?.PoID) {
      //AssignPONumber(response?.data_create_po[0].ponumber);
      $('#POID').val(response?.data_create_po[0]?.PoID ?? '');
      response?.data_create_po[0]?.isCommitAllowed === 1 ? isCommitAllowed=true : isCommitAllowed=false;
      $('#status').val('0');
      ChangeToEditFields();
      toastr.success('Purchase order ' + response.data_create_po[0].PoNumber + ' has been saved!');

      return true;
    } else {
      throw new Error('No po number found in response');
    }
  } catch (error) {
    //what we can do
    return false;
  }

}

function ValidateForm() {
  let accountnum = $("#acnumInput");
  let businessname = $("#bnameInput");
  let items = $('#items-table').DataTable().data();
  let ponumber = $("#ponumber");

  let errors = [];

  if (!ponumber.val()) {
    errors.push("Field 'Account Number' is not filled!");
    ponumber.addClass('invalid-input');
  } else {
    ponumber.removeClass('invalid-input');
  }
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
  if (items.length <= 0) {
    errors.push("At least one item should be in quotation!");
    $('#items-table').parent().addClass('invalid-input');
  } else {
    $('#items-table').parent().removeClass('invalid-input');
  }

  if (errors.length > 0) {
    errors.forEach(function (error) {
      toastr.error(error);
    });
    return false;
  }

  return true;
}

function PrepareMainFields(status=0) {
  return {
    DB: GetDb(),
    poid: $("#POID").val() || '',
    PoNumber: $("#ponumber").val() || '',
    podate: $("#podate").val() || '',
    status: status,
    accountnum: $("#acnumInput").val() || '',
    businessname: $("#bnameInput").val() || '',
    contactname: $("#supplierid").val() || '',
    supplierid: $("#acnumInput").attr('data-id') || '',
    phone: $("#bphone").val() || '',
    notes: $("#notes").val() || '',
    TotQtyOrd: parseFloat($("#totalqty").find("strong").eq(0).text()) || '',
    TotQtyRcv: parseFloat($("#totalqty").find("strong").eq(0).text()) || '',
    POTotal: $('#totalcost strong').text() || '0'
  };
}

function PrepareItemsTable() {
  var table = $("#items-table").DataTable();
  var tableData = table.rows().data().toArray();


  var editedTableData = tableData.map(item => ({ ...item }));

  editedTableData.forEach((item) => {
    delete item.Stock;
    delete item.S;
    delete item.TotalCost;
    delete item.UnitPrice;
    item.Total = parseFloat(item.Total) || '';
    item.QtyOrdered = parseInt(item.Qty) || '';
    item.QtyReceived = item.QtyOrdered || '';
    item.ExtendedCost = 0;

  });

  return editedTableData;
}

async function SetDbDropDown() {
  try {
    const data = await $.ajax({
      url: SourceDBUrl,
      type: "GET",
      traditional: true,
      dataType: "json"
    });

    const db_list = data.items;
    if (Array.isArray(db_list)) {
      const dropdownMenu = $("#dropdownMenu");
      dropdownMenu.empty();

      db_list.forEach(function (item) {
        const dropdownItem = $("<a>")
          .addClass("dropdown-item")
          .text(item.SourceDB)
          .attr("data-value", item.id);


        dropdownItem.off('click');
        dropdownItem.on("click", function () {
          handleDropdownItemClick(item, dropdownItem);


        });

        if (item.id == GetDb()) {
          setActiveDropdownItem(item, dropdownItem);
        }

        dropdownMenu.append(dropdownItem);
      });

      if (db_list.length > 1) {
        $("#dbDropdown").css("display", "block");
      } else if (db_list.length === 1) {
        SetDb(db_list[0].id);
      }

      updateMainPoState();





    }

  } catch (error) {
    console.error("Error fetching data:", error);
    throw error;
  }
}

function handleDropdownItemClick(item, dropdownItem) {
  $("#dropdownMenu .active").removeClass("active");
  $("#dropdownMenuButton").text(item.SourceDB);


  SetDb(item.id);
  $("#modalsearch").attr("disabled", false);
  $("#lookinDropdown").attr("disabled", false);

  setActiveDropdownItem(item, dropdownItem);

  InitDataTable();
  updateMainPoState();
}

function setActiveDropdownItem(item, dropdownItem) {
  $("#dropdownMenuButton")
    .text(item.SourceDB)
    .attr("data-value", item.id);
  dropdownItem.addClass("active");
}

function updateMainPoState() {


  //ChangeToEditFields();
  const mainpo = document.getElementById("mainpo");
  if (mainpo) {
    if (GetDb()) {
      mainpo.style.opacity = 1;
      mainpo.style.pointerEvents = "all";
    } else {
      mainpo.style.opacity = 0.5;
      mainpo.style.pointerEvents = "none";
    }
  }
}

async function SubmitPO(data) {


  return new Promise((resolve, reject) => {
    $.ajax({
      url: model.apiUrl + "/savepo",
      type: "POST",
      data: data,
      traditional: true,
      dataType: "json",
      success: function (response) {
        if (response?.error==1){
          toastr.error(response?.error_info);
          throw new Error(response?.error_info);
        }
        resolve(response);
      },
      error: function (xhr, status, error) {
        toastr.error(error);
        reject(error);
      },
    });
  });
}


async function DeletePOT(POId = null, event) {
  event.preventDefault();
  await DeleteModal(POId, false);
  let table = $('#PO-table-list').DataTable();
  let row = $(event.target).closest('tr');
  table.row(row).remove().draw(false);
}

function DeleteModal(POId = null, redirect = true) {
  return new Promise(resolve => {
    $('#deleteText').text('Do you really want to remove Purchase order?')

    $('#deleteModal').modal('show');
    $('#remove').off('click');
    // Handle delete button click inside the modal
    $('#remove').on('click', async function () {

      await DeletePO(POId, redirect);
      resolve();
    });
  });
}

async function DeletePO(POId = null, redirect = true) {
  let DBname = GetDb();
  let PoID = POId || $('#POID').val();

  let paramsObj = {
    DB: DBname,
    PoID: PoID
  };

  try {
    await $.ajax({
      url: model.apiUrl + "/deletepo",
      type: 'POST',
      data: paramsObj
    });
    toastr.success('Purchase order removed successfully');
    if (redirect) {
      ClosePO();
    }
  } catch (error) {
    toastr.error('An error occurred while removing Purchase order');
  }
}

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


});

function ClosePO() {
  $('#POForm').addClass('modal-blur-bg');

  setTimeout(async () => {
    let href = model.apiUrl.replace('api1/createpurchaseorder', 'purchaseorder');
    window.location.href = href;
  }, 500);


}

async function SaveAndClosePO() {

  $('#submitAndSaveButton').prop('disabled', true);
  $('#submitButton').prop('disabled', true);

  const saveSuccess = await SavePO();
  if (!saveSuccess) {
    $('#submitAndSaveButton').prop('disabled', false);
    $('#submitButton').prop('disabled', false);
    return;
  }

  $('#POForm').addClass('modal-blur-bg');
  setTimeout(async () => {

    ClosePO();
    $('#submitAndSaveButton').prop('disabled', false);
    $('#submitButton').prop('disabled', false);

  }, 500);

}

async function SaveAndPrintPO() {

  let saveSuccess = true;

  if ($('#status').val() != 1) {
    try {
      saveSuccess = await SavePO();
    } catch (error) {
      console.error('Error saving PO:', error);
      saveSuccess = false;
    }
  }

  if (!saveSuccess) {
    return;
  }

  let object = { DBname: GetDb(), PoId: $('#POID').val(), PONumber: $('#ponumber').val() };

  try {
    await PrintPO(object);
  } catch (error) {
    toastr.error('Error printing PO:', error);
    r
  }
}



async function PrintPO(object) {
  let q = {
    DBname: object.DBname || GetDb(),
    PoId: parseInt(object.PoId) || '',
    PONumber: parseInt(object.PONumber) || ''
  }

  try {
    $.ajax({
      url: model.apiUrl + "/printpo",
      type: "POST",
      data: q,
      traditional: true,
      dataType: "json",
      success: function (response) {
        if (response?.data_printpo?.length > 0) {
          $('#pdfViewer').attr('src', 'data:application/pdf;base64,' + response.data_printpo[0].pdfFile);
          $('#printModal').modal('show');
        } else {
          toastr.error("File not found.");
        }
      },
      error: function (xhr, status, error) {
        // Handle error
        console.error(xhr.responseText);
        throw error;
      }
    });
  } catch (error) {
    throw error;
  }

}


async function ConvertToInvoice(object, event = null) {


  let q = {
    DBname: object.DBname || GetDb(),
    QuotationID: parseInt(object.QuotationID),
    QuotationNumber: parseInt(object.QuotationNumber)
  }

  try {
    $.ajax({
      url: model.apiUrl + "/converttoinvoice",
      type: "POST",
      data: q,
      traditional: true,
      dataType: "json",
      success: function (response) {
        if (response?.error==0){
          toastr.error(response?.error_info);
          throw new Error(response?.error_info);
        }

        if (event) {
          ProcessConvert(event);
        }
        else {

          $('#ConvertButton').prop('disabled', true);
          $('#submitAndSaveButton').prop('disabled', true);
          $('#submitButton').prop('disabled', true);
          $('#printButton').prop('disabled', true);

          setTimeout(async () => {

            CloseQuatation();



          }, 800);

        }

        ShowConvertMessage(response.data_converttoinvoice.shift().invoicenumber, q.QuotationNumber);

      },
      error: function (xhr, status, error) {

        console.error(xhr.responseText);
        throw error;
      }
    });
  } catch (error) {
    throw error;
  }




}

function ProcessCommit(event) {
  RemoveCommitButton(event);
  RemoveBoldFont(event);
  ChangeStatus(event);
}

function RemoveCommitButton(event) {
  let row = $(event.target).closest('tr');
  if (row.length > 0) {

    row.find('#CommitButton').html('&nbsp;&nbsp;&nbsp;Commited&nbsp;&nbsp;&nbsp;');
    row.find('#CommitButton').addClass('disabled');
    //$('#CommitButton')

  }
}


function ChangeStatus(event){

  let row = $(event.target).closest('tr');
  if (row.length > 0) {
      row.find('*').each(function() {
      let element = $(this);
      if (element.text().trim() === 'Placed') {
        element.text('Commited');
      }
    });
  }
}
function RemoveBoldFont(event){
  let row = $(event.target).closest('tr');
  if (row.length > 0) {
    //$('#CommitButton')
    row.css('font-weight', 'normal');
  }
}

function ShowCommitMessage(PoNumber) {
  toastr.success('Purchase order '+ PoNumber+ ' has been commited');
}

function ShowCommitModal(object, event = null, save) {
  $('#commitModal').modal('show');

  $('#commit').off('click').on('click', async function() {
    if (save){
      const saved = await SavePO();
      if (saved){
        await CommitPO(object,event);
      }
    }else{
      await CommitPO(object,event);
    }

  });
}






async function CommitPO(object, event = null) {

  let q = {
      DB: object?.DB || GetDb(),
      //POId: parseInt(object.POId),
      status:1,
      PoNumber: object?.PoNumber
    }

  try {
    $.ajax({
      url: model.apiUrl + "/commitpo",
      type: "POST",
      data: q,
      traditional: true,
      dataType: "json",
      success: function (response) {
        if (response?.error==1){
          toastr.error(response?.error_info);
          throw new Error(response?.error_info);
        }
        if (event) {
          ProcessCommit(event);
        }
        else {
          $('#ConvertButton').prop('disabled', true);
          $('#submitAndSaveButton').prop('disabled', true);
          $('#submitButton').prop('disabled', true);
          $('#printButton').prop('disabled', true);

          setTimeout(async () => {

            ClosePO();



          }, 800);

        }

        ShowCommitMessage(q?.PoNumber);



      },
      error: function (xhr, status, error) {
        toastr.error(error)
        console.error(xhr.responseText);
        throw error;
      }
    });
  } catch (error) {
    toastr.error(error)
    throw error;
  }




}
