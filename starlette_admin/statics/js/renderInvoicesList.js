const SALES_REP_INDEX = 7;
const PAYMENT_TERMS_INDEX = 8;
const SHIPPER_INDEX = 9;
const TRACKING_NUMBER_INDEX = 10;
const SHIPPING_COST_INDEX = 11;
const NOTES_INDEX = 12;

var userRoles = [];
var canEdit = false;
var dt_columns = [];

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function getColumnIndexByName(columnName) {
  if (columnName === 'Shipper') {
    return SHIPPER_INDEX;
  }
  if (columnName === 'Payment Terms') {
    return PAYMENT_TERMS_INDEX;
  }
  if (columnName === 'Sales Rep') {
    return SALES_REP_INDEX;
  }
}

function setupDropdownFilter(dropdownSelector, columnName) {
  const columnIndex = getColumnIndexByName(columnName);
  if (columnIndex == null) return;

  const table = $('#example').DataTable();
  const column = table.column(columnIndex);
  const dropdownMenu = $(`${dropdownSelector} .dropdown-menu`);
  const dropdownButton = $(`${dropdownSelector} button`);

  const uniqueValues = column.data().unique().sort();
  dropdownMenu.empty();

  if (uniqueValues.length <= 1) {
    $(dropdownSelector).hide();
    return;
  } else {
    $(dropdownSelector).show();
    dropdownButton.prop('disabled', false);
  }

  uniqueValues.each(function(value) {
    if (value == null || value === '') return;
    const key = columnName.replace(/\s/g, '').toLowerCase();
    const id  = `${dropdownSelector.substring(1)}_check_${escapeRegex(value)}`;
    dropdownMenu.append(`
      <div class="form-check">
        <input
          class="form-check-input filter-${key}"
          type="checkbox"
          value="${value}"
          id="${id}"
        >
        <label class="form-check-label" for="${id}">${value}</label>
      </div>
    `);
  });

  dropdownMenu.append(`
    <div class="form-check">
      <input class="form-check-input" type="checkbox" id="${dropdownSelector.substring(1)}_selectAll">
      <label class="form-check-label" for="${dropdownSelector.substring(1)}_selectAll">Select All</label>
    </div>
  `);

  function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function applyDropdownFilter() {
    const key = columnName.replace(/\s/g, '').toLowerCase();
    const selected = [];
    dropdownMenu.find(`.filter-${key}:checked`).each(function() {
      selected.push($(this).val());
    });

    if (selected.length === 0) {
      column.search('', true, false).draw();
      return;
    }

    const parts = selected.map(v => v === ''
      ? '^$'
      : `^${escapeRegex(v)}$`
    );
    column.search(parts.join('|'), true, false).draw();
  }

  const key = columnName.replace(/\s/g, '').toLowerCase();
  const filterClass = `.filter-${key}`;
  const selectAllSelector = `#${dropdownSelector.substring(1)}_selectAll`;

  dropdownMenu.find(filterClass).on('change', function() {
    const total   = dropdownMenu.find(filterClass).length;
    const checked = dropdownMenu.find(`${filterClass}:checked`).length;
    dropdownMenu.find(selectAllSelector).prop('checked', total === checked);
    applyDropdownFilter();
  });

  dropdownMenu.find(selectAllSelector).on('change', function() {
    const isChecked = $(this).is(':checked');
    dropdownMenu.find(filterClass).prop('checked', isChecked);
    applyDropdownFilter();
  });
}


function fetchUserRoles() {
  $.ajax({
    url: "/api/get_session_info/",
    type: "GET",
    dataType: "json",
    success: function (sessionInfo) {
      var username = sessionInfo.username;
      $.ajax({
        url: "/api/get_user_role/" + username,
        type: "GET",
        dataType: "json",
        success: function (roleInfo) {
          if (typeof roleInfo.roles === "string") {
            userRoles = roleInfo.roles.split("/");
          } else if (Array.isArray(roleInfo.roles)) {
            if (roleInfo.roles.length > 0 && Array.isArray(roleInfo.roles[0])) {
              userRoles = roleInfo.roles.flat();
            } else {
              userRoles = roleInfo.roles;
            }
          } else {
            userRoles = [];
          }
          canEdit = userRoles.includes("admin") || userRoles.includes("manager");
          console.log("Permissions for edit:", canEdit, "Roles:", userRoles);
        },
        error: function (err) {
          console.error("Error occured on roles:", err);
        }
      });
    },
    error: function (err) {
      console.error("Error occured on session:", err);
    }
  });
}

$(document).ready(function () {
  fetchUserRoles();
});

function initializeColumns() {
      let fringe = structuredClone(model.fields);
      let dt_columns = [];
      let dt_fields= [];
      $("#table-header").empty();
      while (fringe.length > 0) {

        let field = fringe.shift(0);

        if (field.type === "CollectionField")
          fringe = field.fields
            .map((f) => {
              f.name = field.name + "." + f.name;
              f.label = field.label + "." + f.label;
              return f;
            })
            .concat(fringe);

        else if (field.type === "EnumField1") {
        }

        else if (field.type === "IntegerField1") {
        }
        else if (field.type === "FloatField1") {
        }
        if (field.identity6) {
        }


        else if (field.type === "ListField") {
          if (field.field.type == "CollectionField") {
            $("#table-header").append(`<th>${field.label}</th>`);
            dt_columns_updated.push({
              name: field.name,
              data: field.name,
              orderable: field.field.orderable,
              searchBuilderType: field.search_builder_type,
              render: function (data, type, full, meta) {

                return render[field.field.render_function_key](
                  data,
                  type,
                  full,
                  meta,
                  field
                );
              },
            });
          } else {
            field.field.name = field.name;
            field.field.label = field.label;
            fringe.unshift(field.field);
          }
        } else if (!field.exclude_from_list) {
          $("#table-header").append(`<th>${field.label}</th>`);
          dt_columns.push({
            name: field.name,
            data: field.name,
            type: field.input_type,
            orderable: field.orderable,
            searchBuilderType: field.search_builder_type,
            render: function (data, type, full, meta) {
              if (["Balance", "InvoiceTotal", "ShippingCost"].includes(field.name)) {
                if (type === 'display' || type === 'filter') {
                  if (isNaN(parseFloat(data))) {
                    return "";
                }
                  return `$${parseFloat(data).toFixed(2)}`;
                }
                return parseFloat(data);
              }

          if (field.name === "ProfitMargin") {
            if (type === 'display' || type === 'filter') {
              return `${parseFloat(data).toFixed(2)+'%'}`;
            }
            return parseFloat(data);
          }


          if (meta.col == 0) {

            if (data.includes(' ')) {
                data = data.split(' ')[0];
            }

            let [month, day, year] = data.split('-');

          if (year && month && day) {

                data = `${month}/${day}/${year}`;
            }

            let dateObj = new Date(data);
            if (isNaN(dateObj.getTime())) {

                return data;
            }

            let monthFormatted = ("0" + (dateObj.getMonth() + 1)).slice(-2);
            let dayFormatted = ("0" + dateObj.getDate()).slice(-2);
            let yearFormatted = dateObj.getFullYear();


            let sortableDate = `${yearFormatted}-${monthFormatted}-${dayFormatted}`;


            let displayDate = `${monthFormatted}/${dayFormatted}/${yearFormatted}`;


            if (type === 'display' || type === 'filter') {
                return displayDate;
            } else {
                return sortableDate;
            }
        }



              return render[field.render_function_key](
                data,
                type,
                full,
                meta,
                field
              );
            },
          });
          dt_fields.push(field);



          if (field.name === "InvoiceNumber") {
            let clonedField = structuredClone(field);
            clonedField.name = "InvoiceID";
            clonedField.label = "InvoiceID";
            dt_columns.push(createColumnConfig(clonedField));
            dt_fields.push(clonedField);
            $("#table-header").append(`<th>${clonedField.label}</th>`);
          }

        }
      };
      dt_columns.push({
        name: "Details",
        data: null,
        orderable: false,
        className: 'text-center sticky-col',
        render: render.col_3
      });
      return { dt_columns: dt_columns, dt_fields: dt_fields };
    };
    function createColumnConfig(field) {
      return {
        name: field.name,
        data: field.name,
        type: field.input_type,
        orderable: field.orderable,
        searchBuilderType: field.search_builder_type,
        render: function (data, type, full, meta) {
          if (field.name === "Balance" || field.name === "InvoiceTotal") {
            if (type === 'display' || type === 'filter') {
              
              return `$${parseFloat(data).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}`;
            }
            return data;
          }

          if (meta.col === 0) {
            if (data.includes(' ')) data = data.split(' ')[0];

            let [month, day, year] = data.split('-');
            if (year && month && day) data = `${month}/${day}/${year}`;

            let dateObj = new Date(data);
            if (isNaN(dateObj.getTime())) return data;

            let sortableDate = `${dateObj.getFullYear()}-${("0" + (dateObj.getMonth() + 1)).slice(-2)}-${("0" + dateObj.getDate()).slice(-2)}`;
            let displayDate = `${("0" + (dateObj.getMonth() + 1)).slice(-2)}/${("0" + dateObj.getDate()).slice(-2)}/${dateObj.getFullYear()}`;

            return type === 'display' || type === 'filter' ? displayDate : sortableDate;
          }

          return render[field.render_function_key](data, type, full, meta, field);
        },
      };
    }

$.fn.dataTable.ext.type.order['custom-date-pre'] = function (date) {
  // Assuming your date format is "MMMM D, YYYY" (e.g., "August 12, 2024")
  var dateParts = date.split(' '); // Split the string by spaces
  var month = dateParts[0];
  var day = parseInt(dateParts[1].replace(',', ''), 10); // Remove the comma and parse the day
  var year = parseInt(dateParts[2], 10);

  // Create a Date object from the parts
  return new Date(year, new Date(Date.parse(month + " 1, 2020")).getMonth(), day);
};

  //for what we need it?
  function initializeButtons (){
    $("#table-header").append(`<th></th>`);

  buttons = [];
  export_buttons = [];
  if (model.exportTypes.includes("csv"))
    export_buttons.push({
      extend: "csv",
      text: function (dt) {
        return `<i class="fa-solid fa-file-csv"></i> ${dt.i18n("buttons.csv")}`;
      },
      exportOptions: {
        columns: model.exportColumns,
        orthogonal: "export-csv",
      },
    });
  if (model.exportTypes.includes("excel"))
    export_buttons.push({
      extend: "excel",
      text: function (dt) {
        return `<i class="fa-solid fa-file-excel"></i> ${dt.i18n(
          "buttons.excel"
        )}`;
      },
      exportOptions: {
        columns: model.exportColumns,
        orthogonal: "export-excel",
      },
    });
  if (model.exportTypes.includes("pdf"))
    export_buttons.push({
      extend: "pdf",
      text: function (dt) {
        return `<i class="fa-solid fa-file-pdf"></i> ${dt.i18n("buttons.pdf")}`;
      },
      exportOptions: {
        columns: model.exportColumns,
        orthogonal: "export-pdf",
      },
    });
  if (model.exportTypes.includes("print"))
    export_buttons.push({
      extend: "print",
      text: function (dt) {
        return `<i class="fa-solid fa-print"></i> ${dt.i18n("buttons.print")}`;
      },
      exportOptions: {
        columns: model.exportColumns,
        orthogonal: "export-print",
      },
    });
  if (export_buttons.length > 0)
    buttons.push({
      extend: "collection",
      text: function (dt) {
        return `<i class="fa-solid fa-file-export"></i> ${dt.i18n(
          "admin.buttons.export"
        )}`;
      },
      className: "",
      buttons: export_buttons,
    });
  noInputCondition = function (cn) {
    return {
      conditionName: function (t, i) {
        return t.i18n(cn);
      },
      init: function (a) {
        a.s.dt.one("draw.dtsb", function () {
          a.s.topGroup.trigger("dtsb-redrawLogic");
        });
      },
      inputValue: function () {},
      isInputValid: function () {
        return !0;
      },
    };
  };
  if (model.columnVisibility)
    buttons.push({
      extend: "colvis",
      text: function (dt) {
        return `<i class="fa-solid fa-eye"></i> ${dt.i18n("buttons.colvis")}`;
      },
    });
  }
// Custom sorting function using moment.min.js for the DateField_dig type




  function extractCriteria(c) {
    var d = {};
    if ((c.logic && c.logic == "OR") || c.logic == "AND") {
      d[c.logic.toLowerCase()] = [];
      c.criteria.forEach((v) => {
        d[c.logic.toLowerCase()].push(extractCriteria(v));
      });
    } else {
      if (c.type.startsWith("moment-")) {
        searchFormat = dt_fields.find(
          (f) => f.name == c.origData
        )?.search_format;
        if (!searchFormat) searchFormat = moment.defaultFormat;
        c.value = [];
        if (c.value1) {
          c.value1 = moment(c.value1).format(searchFormat);
          c.value.push(c.value1);
        }
        if (c.value2) {
          c.value2 = moment(c.value2).format(searchFormat);
          c.value.push(c.value2);
        }
      } else if (c.type == "num") {
        c.value = [];
        if (c.value1) {
          c.value1 = Number(c.value1);
          c.value.push(c.value1);
        }
        if (c.value2) {
          c.value2 = Number(c.value2);
          c.value.push(c.value2);
        }
      }
      cnd = {};
      c_map = {
        "=": "eq",
        "!=": "neq",
        ">": "gt",
        ">=": "ge",
        "<": "lt",
        "<=": "le",
        contains: "contains",
        starts: "startswith",
        ends: "endswith",
        "!contains": "not_contains",
        "!starts": "not_startswith",
        "!ends": "not_endswith",
        null: "is_null",
        "!null": "is_not_null",
        false: "is_false",
        true: "is_true",
      };
      if (c.condition == "between") {
        cnd["between"] = c.value;
      } else if (c.condition == "!between") {
        cnd["not_between"] = c.value;
      } else if (c_map[c.condition]) {
        cnd[c_map[c.condition]] = c.value1 || "";
      }
      d[c.origData] = cnd;
    }
    return d;
  }

function initializeDataTable(dt_columns){

  $('#spinner-container').css({"display": "flex"});
  $('#example thead .filter-row').remove();


  let pageLength = getCookie('pageLength') || 10;


  initializeButtons();

    if ( $.fn.dataTable.isDataTable( '#example' ) ) {
        table = $('#example').DataTable();
    }
    else {
        table = $('#example').DataTable( {
            paging: false
        } );
    }
    RemoveKeyUpDownListeners('example');
    table.destroy();


    new DataTable('#example', {
      dom: '<"newQutation-button"> <"top"f<"clear">>rt<"card-footer d-flex align-items-center justify-content-between custom-footer"lp> <"info">i ',
       scrollX: true,
       autoWidth: false,
       paging: true,
       lengthChange: true,
       searching: true,
       info: true,
       colReorder: true,
       searchHighlight: true,
       pageLength:parseInt(pageLength),


       searchBuilder: {
         delete: `<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-trash" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"></path><line x1="4" y1="7" x2="20" y2="7"></line><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line><path d="M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12"></path><path d="M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3"></path></svg>`,
         left: `<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-chevron-left" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"></path><polyline points="15 6 9 12 15 18"></polyline></svg>`,
         right: `<svg xmlns="http://www.w3.org/2000/svg" class="icon icon-tabler icon-tabler-chevron-right" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"></path><polyline points="9 6 15 12 9 18"></polyline></svg>`,
       },



        ajax: function (data, callback, settings) {

          $('#example_wrapper').css({"display": "none"});
            order = [];
            query = {
              skip: settings._iDisplayStart,
              order_by: order,
              dop: model.dop
            };
            $.ajax({
              url: model.apiUrl,
              type: "get",
              data: query,
              traditional: true,
              dataType: "json",
              success: function (data, status, xhr) {
                data = data.items;
                data.forEach((d) => {
                  d.DT_RowId = d[model.pk];
                  if (d.Total) {
                    d.Total = parseFloat(d.Total).toFixed(2);
                }
                });

                $('#example_wrapper').css({"display": "block"});
                $('#spinner-container').css({"display": "none"});


                callback(  {
                  data: data.sort((a, b) => {

                      // Преобразуем quotationid в число и сравниваем в обратном порядке
                      return Number(b.InvoiceID) - Number(a.InvoiceID);
                  }),
              }
            );
           //
              },
            });


          },
        columns: [...dt_columns],
        columnDefs: [
          { targets: 0, type: 'date' },  // Apply built-in date sorting to the date column
          { targets: 1, type: 'number' },  // Apply built-in date sorting to the date column
          { targets: 2, type: 'text', visible: false},
          { targets: -1, width: "100px" },
      ],

        order: [
          // [0, 'desc'],
          // [1, 'desc']
        ],
      select: true,
      initComplete: function () {


        initDlbClick();
        initEnter();

        setupDropdownFilter('#shipper-dropdown', 'Shipper');
        setupDropdownFilter('#paymentterms-dropdown', 'Payment Terms');
        setupDropdownFilter('#sales-rep-dropdown', 'Sales Rep');

        var table = $('#example').DataTable();
        // Editable Fields Feature.
        $('#example tbody').on('click', 'td', function () {
            var cell = table.cell(this);
            if (!cell || cell.index() === undefined) return;

            var columnIndex = cell.index().column;

            if ([9, 10, 11, 12].includes(columnIndex) && !canEdit) {
              return;
            }
          
            var editableColumns = [TRACKING_NUMBER_INDEX, SHIPPING_COST_INDEX, NOTES_INDEX];
            if (columnIndex === SHIPPER_INDEX) {
              var currentValue = cell.data();
              var dbName = getCookie('DB');
              $.ajax({
                url: `/api/get_shippers/${dbName}/`,
                type: 'GET',
                dataType: 'json',
                success: function (response) {
                  var select = $('<select class="form-control" style="color: black; background-color: white;"></select>');
          
                  var selectedNone = (currentValue === null || currentValue === "" || currentValue === "");
                  select.append(`<option value="" ${selectedNone ? 'selected' : ''}>None</option>`);
          
                  $.each(response.shippers, function (index, shipper) {
                    var selected = (shipper.name === currentValue) ? 'selected' : '';
                    select.append(`<option value="${shipper.id}" ${selected}>${shipper.name}</option>`);
                  });
          
                  $(cell.node()).empty().append(select);
                  select.focus();
          
                  select.on('mousedown click', function (e) {
                    e.stopPropagation();
                  });
          
                  select.on('change blur', function () {
                    var newID = $(this).val();
                    var newName = $(this).find('option:selected').text();
          
                    cell.data(newName).draw();
          
                    updateDatabase(cell, currentValue, newID);
                  });
                },
                error: function (err) {
                  console.error("Ошибка получения списка поставщиков.", err);
                }
              });
              return;
            }

            // another cases
            if (editableColumns.includes(columnIndex)) {
                var oldValue = cell.data();
                var inputType = columnIndex === SHIPPING_COST_INDEX ? 'number' : 'text';
            
                var input = $(`<input type="${inputType}" class="form-control" />`)
                  .val(oldValue)
                  .appendTo($(this).empty())
                  .focus();

                if (columnIndex === SHIPPING_COST_INDEX) {
                  input.on('input', function () {
                    this.value = this.value.replace(/[^0-9.]/g, '');
                  });
                }

                input.on('keypress', function (e) {
                  if (e.which === 13) { // Enter
                    var newValue = $(this).val();
            
                    if (columnIndex === SHIPPING_COST_INDEX && isNaN(parseFloat(newValue))) {
                      return;
                    }
                    var oldValue = cell.data();
                    cell.data(newValue).draw();
                    updateDatabase(cell, oldValue, newValue);
                  }
                });

                input.on('blur', function () {
                  var newValue = $(this).val();
            
                  if (columnIndex === SHIPPING_COST_INDEX && isNaN(parseFloat(newValue))) {
                    return;
                  }
                  var oldValue = cell.data();
                  cell.data(newValue).draw();
                  updateDatabase(cell, oldValue, newValue);
                });
              }
            });

        function updateDatabase(cell, oldValue, newValue) {
          if (typeof oldValue === "number") {
              oldValue = oldValue.toString();
          } else if (typeof oldValue === "string") {
              oldValue = oldValue.trim();
          }
          if (typeof newValue === "number") {
              newValue = newValue.toString();
          } else if (typeof newValue === "string") {
              newValue = newValue.trim();
          }
          
          if (oldValue === newValue) {
              return;
          }

          var dbName = getCookie('DB');
          var rowData = table.row(cell.index().row).data();
          var headerText = table.column(cell.index().column).header().textContent.trim();
          var columnName;
          if (["Tracking number", "TrackingNo"].includes(headerText)) {
              columnName = "TrackingNo";
          } else if (["Shipping Cost", "ShippingCost"].includes(headerText)) {
              columnName = "ShippingCost";
          } else if (["Shipper"].includes(headerText)) {
              columnName = "ShipperID" 
          } else {
              columnName = headerText;
          }

          $.ajax({
              url: `/api/update_invoice_data/${dbName}/?id=${rowData.InvoiceID}&field=${columnName}&value=${newValue}`,
              type: 'GET',
              success: function (response) {
                  console.log('Data has been updated successfully.', response);
              },
              error: function (xhr, status, error) {
                  console.error('Error has been happened.', error);
              }
          });
      }


        let quotationId = getCookie('QuotationID');
        if (quotationId) {
          var table = $('#example').DataTable();
          var row = table.row(function ( idx, data, node ) {

            return data.QuotationID == quotationId;
        } );
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
        setCookie('QuotationID',null);
      }
      AddKeyUpDownListeners('example');
    }
    });

    $('#example')?.DataTable()?.on('length.dt', function(e, settings, len) {
    SetTableLenght(len)
});
}

function initDlbClick(){
  $(document).ready(function() {
    var table = $('#example').DataTable();

    $('#example tbody').on('dblclick', 'tr', function() {
        var clickedRow = $(this);
        var actionLink = clickedRow.find('a:contains("See Details")');

        if (actionLink.length > 0) {
            actionLink[0].click();
        } else {
            console.log("No link for 'view_invoice' in selected row.");
        }
    });
});
}

function initEnter(){
  $(document).on('keydown', function(e) {
    if (e.which === 13) {
        var selectedRow = $('#example tbody tr.selected');

        if (selectedRow.length > 0) {
            var actionLink = selectedRow.find('a:contains("Edit"), a:contains("View")');

            if (actionLink.length > 0) {
                actionLink[0].click();
            } else {
                console.log("Нет ссылки 'Edit' или 'View' в выделенной строке.");
            }
        } else {
            console.log("Нет выделенной строки.");
        }
    }
  });
}

function setSessionStorage() {
  sessionStorage.setItem('modelDop', model.dop);
}

function setCustomerInfo(){
let table= $('#example').DataTable();
let row = table.row('.selected').data()
  if (row){
    let anum =row.AccountNo || ''
    sessionStorage.setItem('anum', anum);
  }
}

$('#example tbody').off('click', '.dropdown');

$('#example tbody').on('click', '.dropdown', function (e) {
  let row = $(this).closest('tr');
  let rowIndex = table.row(row).index();

  table.rows().deselect();
  table.row(rowIndex).select();

});


function updateInfo(table, visibleCount) {
  const info = table.page.info(); // Получаем информацию о странице
  const totalCount = table.data().length; // Общее кол-во записей

  // Формируем новый текст
  const infoText = `Showing ${info.start + 1} to ${info.end} of ${visibleCount} entries (filtered from ${totalCount} total entries)`;

  // Обновляем текст в элементе `example_info`
  $('#example_info').text(infoText);
}

function applyFilter(selectedValues,column) {
  ;
  const escapedValues = selectedValues.map(v => '\\b' + v + '\\b'); // Экранируем границы слова
  var regexval = escapedValues.join('|') || '9999999999'; // Защитное значение

  column.search(regexval, true, false).draw(); // Применяем фильтр

}


$('#convertModal').on('hidden.bs.modal', function (e) {

  if ($.fn.DataTable.isDataTable('#example')) {

      let table = $('#example').DataTable();


      let row = table.row('.selected'); // Ensure the row has the 'selected' class

      // Check if a row is selected
      if (row.any()) {
          // Get the row node
          let rowNode = row.node();

          // Apply the style changes to buttons in the selected row
          $(rowNode).find(".btn-outline-danger").removeClass("btn-outline-danger").addClass("btn-danger");
          $(rowNode).find(".btn-outline-warning").removeClass("btn-outline-warning").addClass("btn-warning");
          $(rowNode).find(".btn-outline-info").removeClass("btn-outline-info").addClass("btn-info");
          $(rowNode).find(".btn-outline-success").removeClass("btn-outline-success").addClass("btn-success");
          $(rowNode).find(".btn-outline-secondary").removeClass("btn-outline-secondary").addClass("btn-secondary");
      } else {
          console.log('No row is selected.');
      }
  } else {
      console.log('DataTable does not exist.');
  }
});