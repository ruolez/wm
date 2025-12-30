/*
  This file contains asynchronous functions for server interaction.
  It includes methods for requesting quotations, fetching browse items,
  setting up the database dropdown, retrieving additional information
  about quotations and businesses, as well as for deleting quotations
  and submitting new quotations.
*/
async function GetQuotation() {
  try {
    let queryParams = new URLSearchParams(window.location.search).toString();
    if (queryParams) {
     let data=  await RequestQuotation(queryParams);
     PopulateQuotationDetails(data);
    }
  } catch (error) {
    toastr.error(error.text);
  }
  }

async function RequestQuotation(queryParams) {
    try {
      const response = await $.ajax({
        url: model.apiUrl + "/getquotation" + '?' + queryParams,
        type: "GET",
        traditional: true,
        dataType: "json",
      });
      return response;
    } catch (error) {
      toastr.error("Error occurred, returning data.");

    }
  }

async function GetBrowseItems(inputValue) {
    let lookinValue = GetDropdownValue("#lookinDropdown");
    let searchData = {
      DB: document
        .getElementById("dropdownMenuButton")
        ?.getAttribute("data-value"),
      searchValue: inputValue,
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

async function SetDbDropDown() {
    return new Promise((resolve, reject) => {
      $.ajax({
        url: newUrl,
        type: "get",
        traditional: true,
        dataType: "json",
        success: function (data, status, xhr) {
          let db_list = data.items;
          if (Array.isArray(db_list)) {
            let dropdownMenu = document.getElementById("dropdownMenu");

            dropdownMenu.innerHTML = "";
            db_list.forEach(function (item) {
              let dropdownItem = document.createElement("a");
              dropdownItem.classList.add("dropdown-item");

              dropdownItem.textContent = item.SourceDB;
              dropdownItem.dataset.value = item.id;

              dropdownItem.addEventListener("click", function (event) {
                document.getElementById("dropdownMenuButton").textContent =
                  item.SourceDB;
                sessionStorage.setItem("modelDop", item.id);
                document.getElementById("mainqtn").style.opacity = 1;
                document.getElementById("mainqtn").style.pointerEvents = "all";
                document.getElementById("actionButtons").style.opacity = 1;
                document.getElementById("actionButtons").style.pointerEvents =
                  "all";
              });

              if (item.id === selectedModelId) {
                document.getElementById("dropdownMenuButton").textContent =
                  item.SourceDB;
                document
                  .getElementById("dropdownMenuButton")
                  ?.setAttribute("data-value", item.id);
                dropdownItem.classList.add("active");
              }

              dropdownMenu.appendChild(dropdownItem);
            });
          }

          if (db_list.length > 1) {
            document.getElementById("dbDropdown").style.display = "block";
          }

          if (!selectedModelId) {
            document.getElementById("mainqtn").style.opacity = 0.5;
            document.getElementById("mainqtn").style.pointerEvents = "none";
            document.getElementById("actionButtons").style.opacity = 0.5;
            document.getElementById("actionButtons").style.pointerEvents = "none";
          }

          resolve();
        },
        error: function (xhr, status, error) {
          console.error("Error fetching data:", error);
          reject(error);
        },
      });
    });
  }

async function GetAdditionalInfo() {
    return new Promise((resolve, reject) => {
      let searchData = {
        DB: sessionStorage.getItem("modelDop"),
      };


      $.ajax({
        url: model.apiUrl + "/createquoatallinfo",
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

async function GetBusneessInfo(inputValue, name) {
    return new Promise((resolve, reject) => {
      let searchData = {
        DB: sessionStorage.getItem("modelDop"),
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

async function SubmitQuatation(data) {


    return new Promise((resolve, reject) => {
      $.ajax({
        url: model.apiUrl + "/savequotation",
        type: "POST",
        data: data,
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

async function DeleteQuotationT(quotationID=null, event) {
    event.preventDefault();
    await DeleteModal(quotationID, false);
    let table = $('#example').DataTable();
    let row = $(event.target).closest('tr');
    table.row(row).remove().draw(false);
  }

function DeleteModal(quotationID=null, redirect=true) {
    return new Promise(resolve => {
        $('#deleteModal').modal('show');

        // Handle delete button click inside the modal
        $('#remove').on('click', async function() {
            await DeleteQuotation(quotationID, redirect);
            resolve();
        });
    });
  }

async function DeleteQuotation(quotationID=null, redirect=true) {
    let DBname = sessionStorage.getItem("modelDop");
    let QuotationID = quotationID || $('#QuotationID').val();

    let paramsObj = {
        DBname: DBname,
        QuotationID: QuotationID
    };

    try {
        await $.ajax({
            url: model.apiUrl + "/deleteeditquotation",
            type: 'POST',
            data: paramsObj
        });
        toastr.success('Quotation removed successfully');
        if (redirect){
            RedirectToList();
        }
    } catch (error) {
        toastr.error('An error occurred while removing quotation');
    }
  }

function GetQuickSearchItem() {
    let searchById = $("#quickSearchButton").attr("data-id");
    let searchBy = $("#quickSearchButton").val();
    let searchValue = $("#quicksearch").val();

    if (!searchById || !searchBy || !searchValue) {
      return Promise.reject("some value is empty");
    }

    let searchData = {
      DB: sessionStorage.getItem("modelDop"),
      searchById: searchById,
      searchBy: searchBy,
      searchValue: searchValue,
    };

    return new Promise(function (resolve, reject) {
      $.ajax({
        url: model.apiUrl + "/browseitemsone",
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

function RedirectToList(){
    let targetNavLink = $('.nav-link').find('.nav-link-title').filter(function() {
      return $(this).text().trim() === 'QUOTATIONS';
    }).closest('.nav-link');
    var href = targetNavLink.attr('href');

    window.location.href = href;
  }

async function SaveQuotation()
  {
    if (!ValidateForm()) {

      return false;
    }

    let header = PrepareMainFields();
    let details = PrepareItemsTable();
        details = AddUnitPriceColumn(details);


    var quotationData = {
      ...header,
      items: JSON.stringify(details)

      };

      try {

        const response = await SubmitQuatation(quotationData);
        if (response.data_create_quotation[0].qnumber) {
          AssignQuotationNumber(response?.data_create_quotation[0].qnumber);
          $('#QuotationID').val(response?.data_create_quotation[0]?.QuotationID ?? '');
          ChangeToEditFields();
          toastr.success('Quotation ' + response.data_create_quotation[0].qnumber + ' has been saved!');



          return true;
        } else {
          throw new Error('No quotation number found in response');
        }
      } catch (error) {
        toastr.error(error);
        console.error(error);
        return false;
      }

  }

async function SaveAndCloseQuotation(){

    $('#submitAndSaveButton').prop('disabled', true);
    $('#submitButton').prop('disabled', true);

    const saveSuccess = await SaveQuotation();
    if (!saveSuccess) {
      $('#submitAndSaveButton').prop('disabled', false);
    $('#submitButton').prop('disabled', false);
      return;
    }


    setTimeout(async () => {

    CloseQuatation();
    $('#submitAndSaveButton').prop('disabled', false);
    $('#submitButton').prop('disabled', false);

    }, 500);

  }

function CloseQuatation(){
    RedirectToList();
  }

async function CreateDeleteLink(){

    let Url = model.apiUrl;
    let apiUrl = Url.replace('/api1','').replace("quotations1_tbl", "quotations2_tbl/delete_quotation");

    let params = $.param(paramsObj);
    return updatedUrl = apiUrl +'?'+ params;

  }

async function PrintQuotation(object) {
    let q  =    {
      DBname: object.DBname||sessionStorage.getItem('modelDop'),
      QuotationID: parseInt(object.QuotationID),
      QuotationNumber:parseInt(object.QuotationNumber)
  }

  try {
    $.ajax({
      url: model.apiUrl + "/print_quotation1",
      type: "POST",
      data: q,
      traditional: true,
      dataType: "json",
      success: function(response) {
        if(response?.data_file_quotation[0]?.pdfFile){
        $('#pdfViewer').attr('src', 'data:application/pdf;base64,' + response.data_file_quotation[0].pdfFile);
        $('#printModal').modal('show');
      }
      },
      error: function(xhr, status, error) {
        // Handle error
        console.error(xhr.responseText);
        throw error;
      }
    });
  } catch (error) {
    throw error;
  }

  }

async function SaveAndPrintQuotation(){

    const saveSuccess = await SaveQuotation();
    if (!saveSuccess) {

      return;
    }
    let object = { modelDop: sessionStorage.getItem('modelDop'), QuotationID: $('#QuotationID').val(), QuotationNumber: $('#qnumber').val() };

    await PrintQuotation(object);

  }

async function ConvertToInvoice(object,event=null)
{

  let q  =    {
    DBname: object.DBname||sessionStorage.getItem('modelDop'),
    QuotationID: parseInt(object.QuotationID),
    QuotationNumber:parseInt(object.QuotationNumber)
}

try {
  $.ajax({
    url: model.apiUrl + "/converttoinvoice",
    type: "POST",
    data: q,
    traditional: true,
    dataType: "json",
    success: function(response) {
      if (event)
      {
        ProcessConvert(event);
      }
     else
     {

      $('#ConvertButton').prop('disabled', true);
      $('#submitAndSaveButton').prop('disabled', true);
      $('#submitButton').prop('disabled', true);
      $('#printButton').prop('disabled', true);

      setTimeout(async () => {

        CloseQuatation();
        $('#ConvertButton').prop('disabled', false);
        $('#submitAndSaveButton').prop('disabled', false);
        $('#submitButton').prop('disabled', false);
        $('#printButton').prop('disabled', false);


        }, 800);

    }

      ShowConvertMessage(response.data_converttoinvoice.shift().invoicenumber,q.QuotationNumber);

    },
    error: function(xhr, status, error) {

      console.error(xhr.responseText);
      throw error;
    }
  });
} catch (error) {
  throw error;
}

  }

function ProcessConvert(event){
  RemoveConvertButton(event);
  }

function RemoveConvertButton(event){
  let row = $(event.target).closest('tr');
  if (row.length > 0) {
    row.find('#ConvertButton').remove();
  }
  }



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
};})

