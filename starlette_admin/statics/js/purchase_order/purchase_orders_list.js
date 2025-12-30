var isCommitAllowed = false;

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
  InitDataTable();

});

function generateData() {
  return {
    data: [],
  };
}


///items table
function InitDataTable() {
  return new Promise(function (resolve, reject) {
    CleanDatable("#PO-table-list");
    if ($.fn.DataTable.isDataTable('#PO-table-list')) {
      $('#PO-table-list').DataTable().destroy();
    }
    var table = new DataTable("#PO-table-list", {
      dom: '<"newPO-button"> <"top"f<"clear">>rt<"card-footer d-flex align-items-center justify-content-between custom-footer"lp> <"info">i ',
      scrollY: true,
      paging: true,
      lengthChange: true,
      pageLength:getCookie('pageLength') || 10,
      searching: true,
      info: true,
      colReorder: true,
      searchHighlight: true,
      select: true,
      searchBuilder: {
        delete: `<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-trash" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"></path><line x1="4" y1="7" x2="20" y2="7"></line><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line><path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12"></path><path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3"></path></svg>`,
        left: `<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-chevron-left" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"></path><polyline points="15 6 9 12 15 18"></polyline></svg>`,
        right: `<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-chevron-right" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"></path><polyline points="9 6 15 12 9 18"></polyline></svg>`,
      },
      ajax: function (data, callback, settings) {
        if (GetDb()) {
          RequestPoList()
            .then(function (response) {
              isCommitAllowed = isCommitAllowed = response?.isCommitAllowed === 1 ? true : false;

              let mdata = {
                data: response.data_getpolist
              };
              callback(mdata);
              resolve();

            })
            .catch(function (error) {
              console.error("Error fetching data:", error);
              reject(error);
            });
        } else {
          callback(generateData());
        }
      },
      columns: [
        {
          className: 'details-control',
          orderable: false,
          data: null,
          defaultContent: '',
          title: '',
          render: function () {
            return '<span class="arrow" style="display: flex; justify-content: center; align-items: center;">' +
                   '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" class="icon icon-tabler icons-tabler-filled icon-tabler-caret-down rotate-0">' +
                   '<path stroke="none" d="M0 0h24v24H0z" fill="none" />' +
                   '<path d="M18 9c.852 0 1.297 .986 .783 1.623l-.076 .084l-6 6a1 1 0 0 1 -1.32 .083l-.094 -.083l-6 -6l-.083 -.094l-.054 -.077l-.054 -.096l-.017 -.036l-.027 -.067l-.032 -.108l-.01 -.053l-.01 -.06l-.004 -.057v-.118l.005 -.058l.009 -.06l.01 -.052l.032 -.108l.027 -.067l.07 -.132l.065 -.09l.073 -.081l.094 -.083l.077 -.054l.096 -.054l.036 -.017l.067 -.027l.108 -.032l.053 -.01l.06 -.01l.057 -.004l12.059 -.002z" />' +
                   '</svg>' +
                   '</span>';
          }
        },

        {
          data: "PONumber",
          title: "Number"
        },
        {
          data: "PODate",
          title: "Date",
          type: 'date',
          render: function (data, type, row) {
            var formattedDate = moment(data, 'MM-DD-YYYY').format('MM/DD/YYYY');
            return formattedDate;
          }
        },
        { data: "Supplier" },
        {
          data: "POTotal",
          title: "Total",
          render: function (data, type, row) {
            return '$' + parseFloat(data).toFixed(2);
          }
        },
        {
          data: "Status",
          title: "Status",
          render: function (data, type, row) {
            return row.Status == 0 ? "Placed" : "Committed";
          }
        },
        {
          orderable: false,
          render: function (data, type, row) {
            let apiurl = model.apiUrl;
            apiurl = apiurl.replace("api1/purchaseorder", "createpurchaseorder");
            let editButton = `
              <a href="${apiurl}?DBname=${GetDBid()}&POId=${row.POID}&PoNumber=${row.PONumber}" onclick="">
                <button type="button" class="btn btn-outline-success" style="font-size: 10px;">
                  Edit
                </button>
              </a>
            `;
            let commitButton;

            if (isCommitAllowed){
              if (row.Status == 0) {

                commitButton = `
                  <button type="button" class="btn btn-outline-warning" style="font-size: 10px;" id="CommitButton" onclick="ShowCommitModal({ DB: '${GetDBid()}', PoNumber: '${row.PONumber}',status:1 }, event, false)">
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Commit&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                  </button>
                `;
              } else
              {
                commitButton = `
                  <button type="button" class="btn btn-outline-warning disabled" style="font-size: 10px;" id="CommitButton">
                    &nbsp;&nbsp;&nbsp;Commited&nbsp;&nbsp;&nbsp;
                  </button>
                `;
              }
            }

            else{
              if (row.Status == 1) {
                commitButton = `
                <button type="button" class="btn btn-outline-warning disabled" style="font-size: 10px;" id="CommitButton">
                  &nbsp;&nbsp;&nbsp;Commited&nbsp;&nbsp;&nbsp;
                </button>
              `;

              } else {
                commitButton = `
                  <button type="button" class="btn btn-outline-warning disabled" style="font-size: 10px;" id="CommitButton" onclick="ShowCommitModal({ DB: '${GetDBid()}', PoNumber: '${row.PONumber}',status:1 }, event, false)">
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Commit&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                  </button>
                `;
              }
            }

            let printButton = `
              <button type="button" class="btn btn-outline-info" style="font-size: 10px;" id="PrintButton" onclick="PrintPO({ DBname: '${GetDBid()}', PoId: '${row.POID}', PONumber: '${row.PONumber}' })">
                Print
              </button>
            `;
            let deleteButton;
            if (row.Status ==1){
              deleteButton = `
              <button type="button" class="btn btn-outline-danger disabled" style="font-size: 10px;" id="DeleteButton" onclick="DeletePOT(${row.POID}, event)">
                Delete
              </button>
            `;
            }else{
               deleteButton = `
              <button type="button" class="btn btn-outline-danger" style="font-size: 10px;" id="DeleteButton" onclick="DeletePOT(${row.POID}, event)">
                Delete
              </button>
            `;
            }


            return `
              ${editButton}
              ${commitButton}
              ${printButton}
              ${deleteButton}
            `;
          },
        }
      ],
      order: [[2, 'desc']],
      columnDefs: [
        {
          target: 0,
          visible: true,
          width: "2%",
          orderable:false
        },],
        createdRow: function(row, data, dataIndex) {
          if (data.Status == 0) {
            $(row).css('font-weight', 'bold');
          }
        },
      drawCallback: function (settings) {
        let api = this.api();
        let rows = api.rows({ page: 'current' }).nodes();

        api.rows({ page: 'current' }).every(function (rowIdx, tableLoop, rowLoop) {
          let rowData = this.data();
          let row = $(this.node());


          let notesRow = $('<tr class="notes-row"><td colspan="6">' + (rowData.Notes || '') + '</td></tr>');
          row.after(notesRow);


          row.find('.details-control').on('click', function () {
            let icon = $(this).find('.icon-tabler-caret-down');


            if (icon.hasClass('rotate-0')) {
              icon.removeClass('rotate-0').addClass('rotate-90');
            } else {
              icon.removeClass('rotate-90').addClass('rotate-0');
            }


            notesRow.toggle();
          });
        });
      }



    });
    $('.newPO-button').html(`<a href="${newUrl}" class="btn btn-primary">New Purchase Order</a>`);
    $('.newPO-button').on('click', function () {

      SetDb( GetDBid());
      window.location.href = newUrl;
    });



    table.on('length.dt', function(e, settings, len) {
      SetTableLenght(len);
    });
  });
}






async function RequestPoList(){
  return await GetPoList();
}

async function GetPoList(){

    let DBname = GetDb();
    let paramsObj = {
        DB: DBname
    };


    try {
      let response = await $.ajax({
        url: model.apiUrl + "/getpolist",
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



  $(document).ready(function() {
    SetupRowClickHandler("PO-table-list");
  });


 function GetDBid(){
    return $('#dropdownMenuButton').attr('data-value')?? "";
  }