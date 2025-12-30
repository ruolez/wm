/*
  This file contains asynchronous functions for server interaction.
  It includes methods for requesting quotations, fetching browse items,
  setting up the database dropdown, retrieving additional information
  about quotations and businesses, as well as for deleting quotations
  and submitting new quotations.
*/


const NEW_QUOTATION_LABEL = 'NEW QUOTATION';


async function GetQuotation() {
  try {
    let queryParams = new URLSearchParams(window.location.search).toString();
    if (queryParams) {
      $('.dataTables_empty').text('Loading Items....');
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
        DB: GetDb(),
        searchValue: inputValue,
        anum: $("#acnumInput").val() || ""
    };
    searchData = Object.assign({}, searchData, lookinValue);

    try {
        // Отмена предыдущего запроса, если он ещё в процессе
        if (currentRequest) {
            currentRequest.abort();
        }

        // Сохраняем текущий запрос
        currentRequest = $.ajax({
            url: model.apiUrl + "/browseitems",
            type: "POST",
            data: searchData,
            traditional: true,
            dataType: "json"
        });

        let response = await currentRequest;
        return response;
    } catch (error) {
        // Проверяем, был ли запрос отменён
        if (error.statusText !== 'abort') {
            throw error;
        }
    } finally {
        currentRequest = null; // Обнуляем текущий запрос, когда он завершён
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

                SetDb(item.id);
                document.getElementById("mainqtn").style.opacity = 1;
                document.getElementById("mainqtn").style.pointerEvents = "all";

                document.getElementById("actionButtonsWrapper").style.opacity = 1;
                document.getElementById("actionButtonsWrapper").style.pointerEvents =
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
          else if (db_list.length==1)
           {

            SetDb(db_list[0].id);
          }

          if (!selectedModelId) {
            document.getElementById("mainqtn").style.opacity = 0.5;
            document.getElementById("mainqtn").style.pointerEvents = "none";

            document.getElementById("removeButtonWrapper").style.opacity = 0.5;
            document.getElementById("removeButtonWrapper").style.pointerEvents = "none";

            document.getElementById("actionButtonsWrapper").style.opacity = 0.5;
            document.getElementById("actionButtonsWrapper").style.pointerEvents = "none";

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
        DB: GetDb(),
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

async function SubmitQuotation(data) {
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

async function DeleteQuotationT(quotationID=null, event, rowindex) {
    event.preventDefault();
    await DeleteModal(quotationID, false,rowindex);
    let table = $('#example').DataTable();
    if (table){
      let row = $(event.target).closest('tr');
      table.row(row).remove().draw(false);
    }

  }

  function DeleteModal(quotationID=null, redirect=true, rowindex) {
    return new Promise(resolve => {
        $('#deleteText').text('Do you really want to remove Quotation?');
        $('#deleteModal').off('shown.bs.modal');
        $('#deleteModal').modal('show');

        // Когда модальное окно показано, выполняем действия
        $('#deleteModal').on('shown.bs.modal', function () {
            if (rowindex !== undefined && rowindex !== null) {
                let table = $('#example').DataTable();
                // Делаем выбор строки
                table.row(rowindex).select();

                let row = table.row(rowindex);

                if (row.length > 0) {
                  row.select()
                  .show()
                  .draw(false);

                  $(row.node()).find(".btn-outline-danger").removeClass("btn-outline-danger").addClass("btn-danger");
                  $(row.node()).find(".btn-outline-warning").removeClass("btn-outline-warning").addClass("btn-warning");
                  $(row.node()).find(".btn-outline-info").removeClass("btn-outline-info").addClass("btn-info");
                  $(row.node()).find(".btn-outline-success").removeClass("btn-outline-success").addClass("btn-success");
                  $(row.node()).find(".btn-outline-secondary").removeClass("btn-outline-secondary").addClass("btn-secondary");

            }}
        });

        // Отключаем предыдущие обработчики клика перед установкой нового
        $('#remove').off('click').on('click', async function() {
            // Выполняем удаление и разрешаем промис
            await DeleteQuotation(quotationID, redirect);
            resolve();
            // Закрываем модальное окно после удаления
            $('#deleteModal').modal('hide');
        });
    });
}

async function DeleteQuotation(quotationID=null, redirect=true) {
    let DBname = GetDb();
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
          CloseQuatation();
        }
    } catch (error) {
        toastr.error('An error occurred while removing quotation');
    }
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
      var current_label =  $('#labelH1').text().trim()
      
      if (current_label === NEW_QUOTATION_LABEL) {
            $('#submitButton').prop('disabled', true);
            $('#submitAndSaveButton').prop('disabled', true);
            $('#printButton').prop('disabled', true);
      }

      try {

        const response = await SubmitQuotation(quotationData);
        if (response.data_create_quotation[0].qnumber) {
          AssignQuotationNumber(response?.data_create_quotation[0].qnumber);
          $('#QuotationID').val(response?.data_create_quotation[0]?.QuotationID ?? '');
          ChangeToEditFields();
          toastr.success('Quotation ' + response.data_create_quotation[0].qnumber + ' has been saved!');

          $("#invoiceLabel").text( response?.data_create_quotation[0]?.status_quotation?.toString() );
          $('#invoiceLabel').removeClass('display-none');
          if (isChanged!=undefined && isChanged!=null ){
            isChanged = false;

            let $changedLabel = $('#changedLabel');
            if ($changedLabel.length > 0) {
              $changedLabel.hide();
            }

          }
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

async function SaveAndCloseQuotation(href=null){

    $('#submitAndSaveButton').prop('disabled', true);
    $('#submitButton').prop('disabled', true);
    $('#ToProgressButton').prop('disabled', true);
    $('#ConvertButton').prop('disabled', true);
    $('#printButton').prop('disabled', true);
    const saveSuccess = await SaveQuotation();
    if (!saveSuccess) {
    $('#submitAndSaveButton').prop('disabled', false);
    $('#ConvertButton').prop('disabled', false);
    $('#submitButton').prop('disabled', false);
    $('#ToProgressButton').prop('disabled', false);
    $('#printButton').prop('disabled', false);
      return;
    }


    setTimeout(async () => {

    CloseQuatation(href);
    $('#submitAndSaveButton').prop('disabled', false);
    $('#submitButton').prop('disabled', false);
    $('#ToProgressButton').prop('disabled', false);
    $('#ConvertButton').prop('disabled', false);
    $('#printButton').prop('disabled', false);

    }, 500);

  }

function CloseQuatation(link=null){
   $('#quotationForm').addClass('modal-blur-bg');
    // RedirectToList('Quotations');
    setTimeout(async () => {
      let href;
      if (link){
        href = link;
      }else{
        href = model.apiUrl.replace('api1/quotations1_tbl', 'quotations2_tbl');
      }



      window.location.href = href;
    }, 100);


  }

async function CreateDeleteLink(){
    let Url = model.apiUrl;
    let apiUrl = Url.replace('/api1','').replace("quotations1_tbl", "quotations2_tbl/delete_quotation");

    let params = $.param(paramsObj);
    return updatedUrl = apiUrl +'?'+ params;

  }

  async function PrintQuotation(object,rowindex=null) {
    let q = {
        DBname: object.DBname || GetDb(),
        QuotationID: object.QuotationID|| $('#QuotationID').val()||0,
        QuotationNumber: object.QuotationNumber||$('#qnumber').val()||0,
        SetToProgress: parseInt(object.SetToProgress)||0
    };

    return new Promise((resolve, reject) => {
        $.ajax({
            url: model.apiUrl + "/print_quotation1",
            type: "POST",
            data: q,
            traditional: true,
            dataType: "json",success: function(response) {
              if (response?.data_file_quotation[0]?.pdfFile) {
                  $('#pdfViewer').attr('src', 'data:application/pdf;base64,' + response.data_file_quotation[0].pdfFile);

                  const modalPromise = new Promise((resolve) => {
                      $('#printModal').on('shown.bs.modal', function() {


                          resolve(response);
                      });
                  });

                  $('#printModal').modal('show');
                  let invoiceLabel = $('#invoiceLabel');
                  if (invoiceLabel.length) {
                      invoiceLabel.text(response?.data_file_quotation[0]?.status_quotation?.toString());
                      invoiceLabel.removeClass('display-none');
                  }
                  if (rowindex!=undefined){


                    let table = $('#example').DataTable();
                    table.row(rowindex).select();
                    let row = table.row(rowindex);
                    if (row.length > 0) {
                      row.select()
                      .show()
                      .draw(false);

                      $(row.node()).find(".btn-outline-danger").removeClass("btn-outline-danger").addClass("btn-danger");
                      $(row.node()).find(".btn-outline-warning").removeClass("btn-outline-warning").addClass("btn-warning");
                      $(row.node()).find(".btn-outline-info").removeClass("btn-outline-info").addClass("btn-info");
                      $(row.node()).find(".btn-outline-success").removeClass("btn-outline-success").addClass("btn-success");
                      $(row.node()).find(".btn-outline-secondary").removeClass("btn-outline-secondary").addClass("btn-secondary");
                    }



                  }




              }
          },
            error: function(xhr, status, error) {
                console.error(xhr.responseText);
                reject(error);
            }
        });
    });
}


async function SaveAndPrintQuotation(save=true, reload = false){




    let object = { modelDop: GetDb(), QuotationID: $('#QuotationID').val(), QuotationNumber: $('#qnumber').val()};

    if (save){
      await SetInProgressModal(object,save,$('#invoiceLabel').text().toString().toLowerCase().replace(/\s+/g, reload));
    }
    else{
      await SetInProgressModal(object,save,$('#invoiceLabel').text().toString().toLowerCase().replace(/\s+/g, reload));
    }


   // await PrintQuotation(object);

  }

async function ConvertToInvoice(object,event=null, rowindex=null)
{


  let q  = {
    DBname: object.DBname || GetDb(),
    QuotationID: object.QuotationID|| $('#QuotationID').val()||0,
    QuotationNumber: object.QuotationNumber||$('#qnumber').val()||0,
    shipVia: object.shipVia || 0,
    trackingNo: object.trackingNo || 0,
    shippingCost: object.shippingCost|| 0,
    notes:object.notes || 0,
    invoiceType:object.invoiceType
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
        ProcessConvert(event,rowindex);
      }
     else
     {

      $('#ConvertButton').prop('disabled', true);
      $('#ToProgressButton').prop('disabled', true);
      $('#submitAndSaveButton').prop('disabled', true);
      $('#submitButton').prop('disabled', true);
      $('#printButton').prop('disabled', true);

      setTimeout(async () => {

        CloseQuatation();



        }, 800);

    }

      ShowConvertMessage(response.data_converttoinvoice.shift().invoicenumber,q.QuotationNumber);

    },
    error: function(xhr, status, error) {

      toastr.error(xhr.responseText);
      throw error;
    }
  });
} catch (error) {
  throw error;
}




}

function ProcessConvert(event,rowindex=null){

  DisableButtonInRow(event,'ConvertButton');
  UpdateStatusInRow(event);

  if (rowindex!=null && rowindex!= undefined){
    let table = $('#example').DataTable();
    let row = table.row(rowindex);
    row.select();

    $(row.node()).find('.dropdown').find('.btn').prop('textContent','Converted');
    $(row.node()).find('.dropdown').find('.btn').prop('disabled','true');

  }
 // DisableButtonInRow(event,'ToProgressButton');
  //initializeDataTable(initializeColumns().dt_columns);
  }

  function DisableButtonInRow(event, buttonName='ConvertButton') {
    let row = $(event.target).closest('tr');
    if (row.length > 0) {
      row.find('#' + buttonName).prop('disabled', true);
    }
  }


  function EnableButtonInRow(event, buttonName='ConvertButton') {
    let row = $(event.target).closest('tr');
    if (row.length > 0) {
      row.find('#' + buttonName).prop('disabled', false);
    }
  }

  function UpdateStatusInRow(event) {

    let row = $(event.target).closest('tr');
    if (row.length > 0) {
      // Find the span element with data-toggle="tooltip" and text "Placed"
      let statusSpan = row.find('span[data-toggle="tooltip"]').filter(function() {
        return $(this).text().trim().toLowerCase()==='inprogress'||$(this).text().trim().toLowerCase()==='locked'|| $(this).text().trim().toLowerCase()==='on hold' ||$(this).text().trim().toLowerCase()==='onhold';
      });

      if (statusSpan.length > 0) {
        statusSpan.text('Converted');
        statusSpan.attr('title', 'Converted');
      }
    }
  }

  async function SetInProgressModal(object, save = false, status = '', reload = false, rowindex) {
    object.SetToProgress = 1;

    if (save) {
      const saveSuccess = await SaveQuotation(true);
      if (!saveSuccess) {
        return;
      }
    }

    try {
      await PrintQuotation(object, rowindex);
    } catch (error) {
      toastr.error(error);
    }
  }






function ShowConvertMessage(invoicenumber, quotationNumber){
  toastr.success('Quotation ' + quotationNumber+ ' has been converted to invoice '+invoicenumber);
  }

  async function ShowConvertModal(object, event = null, save, rowindex) {

    try {

      let obj = {
        DB: $('#DB').attr('data-value') || getCookie('DB')
      };

      const shippers = await FetchShippers(obj);

      if (event){
        let table = $('#example').DataTable();
        table.rows().deselect();
        if (rowindex !== undefined) {
          let row = table.row(rowindex).select();

          // Меняем стили для выделенной строки
          $(row.node()).find(".btn-outline-danger").removeClass("btn-outline-danger").addClass("btn-danger");
          $(row.node()).find(".btn-outline-warning").removeClass("btn-outline-warning").addClass("btn-warning");
          $(row.node()).find(".btn-outline-info").removeClass("btn-outline-info").addClass("btn-info");
          $(row.node()).find(".btn-outline-success").removeClass("btn-outline-success").addClass("btn-success");
          $(row.node()).find(".btn-outline-secondary").removeClass("btn-outline-secondary").addClass("btn-secondary");
        }
      }
      $('#convertModal').modal('show');


      renderShippersDropdown(shippers?.data);
      let shipviaid;
      // Получаем ID способа доставки из выделенной строки
      if (event){
        let table = $('#example').DataTable();
        let selectedRowData = table.rows({ selected: true }).data();
        if (selectedRowData.length > 0) {
          shipviaid= selectedRowData[0].Ship_Via[0].id;
        }

      }else
      {
        shipviaid =Number($('#shipvDropdown').attr('data-value'))
      }



      // Обновляем выпадающий список
      let $dropdownMenu = $("#shipviadropdown-menu-modal");
      let $dropdownItem = $dropdownMenu.find(`[data-value='${shipviaid}']`);
      if ($dropdownItem.length > 0) {
        let text = $dropdownItem.text();
        $("#shipvDropdown-modal").text(text).attr("data-value", shipviaid);
      }

      CheckForUPS(shipviaid);



      // После подготовки данных показываем модальное окно


    } catch (error) {
      console.error("Error: ", error);
    }

    // Обработчик для кнопки конвертации внутри модального окна
    $('#convert').off('click').on('click', async function () {
      if (object) {

        object.shipVia = parseInt($("#shipvDropdown-modal").attr("data-value") || 0);
        object.trackingNo = $('#trackingNumber').val() || '';
        object.shippingCost = $('#shipingCost').val() || '';
        object.notes = $('#invoiceNotes').val() || '';
        object.invoiceType = $('#scInvoiceCheckbox').is(':checked') ? 'sc' : '';
      }

      if (save) {
        const saved = await SaveQuotation();
        if (saved) {
          await ConvertToInvoice(object, event);
        }
      } else {
        await ConvertToInvoice(object, event, rowindex);
      }
    });



  }

async function GetUpdatedStock(items){

  let DBname = GetDb();


  let paramsObj = {
      DB: DBname,
      items: JSON.stringify(items)
  };


  try {
    let response = await $.ajax({
      url: model.apiUrl + "/updatestock",
      type: "POST",
      data: paramsObj,
      traditional: true,
      dataType: "json",
    });
    return response;
  } catch (error) {
    throw error;
  }
}

async function SetProgress(object, event = null) {
  if (event) {
    DisableButtonInRow(event, 'ToProgressButton');
  }

  let paramsObj = {
    DB: GetDb(),
    QuotationNumber: object.QuotationNumber
  };

  try {
    const response = await $.ajax({
      url: model.apiUrl + "/setprogress",
      type: "POST",
      data: paramsObj,
      traditional: true,
      dataType: "json"
    });

    if (response?.data_set_progress?.error == 0) {
      if (event) {
        UpdateStatusInRow(event);
      }
      toastr.success('Quotation ' + paramsObj.QuotationNumber + ' has been sent to progress');
      return true;
    } else {
      toastr.error(response?.data_set_progress?.error_info);
      return false;
    }
  } catch (error) {
    if (event) {
      EnableButtonInRow(event, 'ToProgressButton');
    }
    toastr.error(error);
    return false;
  }
}

async function GetUpdatedPriceLevel(items,Anum,PriceLevel) {
  let q = {
    DB: GetDb(),
    Pricelevel: PriceLevel,
    anum: Anum,
    Items: JSON.stringify(items, null, 2)
};

  return new Promise((resolve, reject) => {
      $.ajax({
          url: model.apiUrl + "/updatepricelevel",
          type: "POST",
          data: q,
          traditional: true,
          dataType: "json",
          success: function(response) {
              if (response){
                resolve(response);
              }
              else{
                reject(error);
              }

          },
          error: function(xhr, status, error) {
              console.error(xhr.responseText);
              reject(error);
          }
      });
  });
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
      showDuration: '450',
      hideDuration: '400',
      timeOut: '1000',
      extendedTimeOut: '200',
      showEasing: 'swing',
      hideEasing: 'linear',
      showMethod: 'fadeIn',
      hideMethod: 'fadeOut'
};})


async function UpdateQuotationStatus(object) {
  const q = {
    DBname: object.DBname || GetDb(),
    QuotationID: object.QuotationID || 0,
    QuotationNumber: object.QuotationNumber || '',
    OldStatus: object.OldStatus,
    NewStatus: object.NewStatus,
  };

  return new Promise((resolve, reject) => {
    $.ajax({
      url: model.apiUrl + "/updatequtationstatus",
      type: "POST",
      data: q,
      traditional: true,
      dataType: "json",
      success: function (response) {
        if (response?.data_updatequtationstatus?.error == 1) {
          toastr.error(response?.error_info);
          reject(new Error(response?.error_info || "an Error"));
        } else {
          resolve(response);
        }
      },
      error: function (xhr, status, error) {
        reject(new Error(error || "Network error"));
      },
    });
  });
}

async function UnlockQuotation(object){

  return new Promise((resolve, reject) => {
    $.ajax({
        url: model.apiUrl + "/removeReadOnly",
        type: "POST",
        data: object,
        traditional: true,
        dataType: "json",
        success: function(response) {
            if (response){
              resolve(response);
            }
            else{
              reject(error);
            }

        },
        error: function(xhr, status, error) {
            console.error(xhr.responseText);
            reject(error);
        }
    });
});


}


function FetchShippers(object){

  return new Promise((resolve, reject) => {
    $.ajax({
        url: model.apiUrl + "/shippers",
        type: "POST",
        data: object,
        traditional: true,
        dataType: "json",
        success: function(response) {
            if (response){
              resolve(response);
            }
            else{
              reject(error);
            }

        },
        error: function(xhr, status, error) {
            console.error(xhr.responseText);
            reject(error);
        }
    });
});
}


async function GetQoutationDetails(object) {
  return new Promise((resolve, reject) => {
    let Data = {
      DB: object.Db,
      AccountNumber: object.AccountNumber,
      Items:object.Items
    };
    $.ajax({
      url: model.apiUrl + "/productDetails",
      type: "POST",
      data: Data,
      traditional: true,
      dataType: "json",
      success: function (response) {
        resolve(response?.data);
      },
      error: function (xhr, status, error) {
        resolve([]);
        // reject(error);
      },
    });
  });
}

