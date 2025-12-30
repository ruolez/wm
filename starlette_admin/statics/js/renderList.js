

var dt_columns = [];

///remove this

function initializeColumns() {

  ///remove this
  if (model.fields.length > 0 && model.fields[model.fields.length - 1].name === "StatusQuotation") {
    model.fields.pop();
  }

  // end


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
              // Обработка для поля "Total"
              if (field.name === "Total") {
                if (type === 'display' || type === 'filter') {
                  // Форматируем значение как валюту
                  return `$${parseFloat(data).toFixed(2)}`; // Форматируем с символом доллара
                }
                return parseFloat(data); // Оригинальное значение для сортировки
              }


          // Обработка для поля "ProfitMargin"
          if (field.name === "ProfitMargin") {
            if (type === 'display' || type === 'filter') {
              // Handle null/undefined values
              if (data === null || data === undefined) {
                return '0.00%';
              }
              const value = parseFloat(data);
              if (isNaN(value)) {
                return '0.00%';
              }
              return `${value.toFixed(2)}%`;
            }
            // For sorting, return numeric value (null/NaN becomes 0)
            const numValue = parseFloat(data);
            return isNaN(numValue) ? 0 : numValue;
          }


          if (meta.col == 0) {  // Предполагаем, что дата находится в первом столбце (индекс 0)

            if (data.includes(' ')) {
                // Обрезаем время, оставляя только дату
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



          if (field.name === "QuotationNumber") {
            let clonedField = structuredClone(field);
            clonedField.name = "QuotationID";
            clonedField.label = "QuotationID";
            dt_columns.push(createColumnConfig(clonedField));
            dt_fields.push(clonedField);
            $("#table-header").append(`<th>${clonedField.label}</th>`);
          }

        }
      }




      $("#table-header").append(`<th><strong>Status</strong></th>`);
      ;
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
          // Форматирование Total как валюты.
          if (field.name === "Total") {
            if (type === 'display' || type === 'filter') {
              return `$${parseFloat(data).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}`;
            }
            return data; // Оригинальное значение для сортировки.
          }

          // Форматирование даты.
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


    var table = new DataTable('#example', {
      dom: '<"newQutation-button"> <"top custom-search-container"<"clear">>rt<"card-footer d-flex align-items-center justify-content-between custom-footer"lp> <"info">i ',

       serverSide: true,
       paging: true,
       lengthChange: true,
       searching: false,
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
            data.order.forEach((o) => {
              const { column, dir } = o;
              order.push(`${data.columns[column].data} ${dir}`);
            });

            // Read filter states from UI checkboxes (source of truth)
            // Fall back to cookies only if UI elements don't exist yet (initial load)
            let selectedSalesReps = [];
            let selectedStatuses = [];

            // Get sales reps from UI checkboxes
            const salesRepCheckboxes = $('#sales-rep-dropdown .form-check-input.sales-rep:checked');
            if (salesRepCheckboxes.length > 0) {
              // UI exists - read from checkboxes
              selectedSalesReps = salesRepCheckboxes.map(function() {
                return $(this).val();
              }).get();
            } else {
              // UI not ready yet - fall back to cookie for initial load
              const salesRepFilter = getFilterStateFromCookie('salesRepFilterState');
              selectedSalesReps = salesRepFilter
                .filter(item => Object.values(item)[0] === 1)
                .map(item => Object.keys(item)[0]);
            }

            // Get statuses from UI checkboxes
            const statusCheckboxes = $('#status-dropdown .form-check-input.st:checked');
            if (statusCheckboxes.length > 0) {
              // UI exists - read from checkboxes
              selectedStatuses = statusCheckboxes.map(function() {
                return $(this).val();
              }).get();
            } else {
              // UI not ready yet - fall back to cookie for initial load
              const statusFilter = getFilterStateFromCookie('Statuses');
              selectedStatuses = statusFilter
                .filter(item => Object.values(item)[0] === 1)
                .map(item => Object.keys(item)[0]);
            }

            query = {
              skip: settings._iDisplayStart,
              limit: settings._iDisplayLength,
              order_by: order,
              dop: model.dop
            };

            // Add search term from custom input if provided
            const searchValue = $('#customSearch').val();
            if (searchValue) {
              query.search = searchValue;
            }

            // Add filters to query if any are selected
            if (selectedSalesReps.length > 0) {
              query.sales_rep = selectedSalesReps;
            }
            if (selectedStatuses.length > 0) {
              query.status = selectedStatuses;
            }

            // Debug: Log what we're sending
            console.log('🔍 FILTERS SENT:', {
              sales_rep: selectedSalesReps,
              status: selectedStatuses,
              skip: query.skip,
              limit: query.limit
            });
            $.ajax({
              url: model.apiUrl,
              type: "get",
              data: query,
              traditional: true,
              dataType: "json",
              success: function (response, status, xhr) {
                var items = response.items;
                var total = response.total || items.length;

                // Store unique sales reps from response for dropdown population
                if (response.unique_sales_reps) {
                  window.uniqueSalesReps = response.unique_sales_reps;
                }

                items.forEach((d) => {
                  d.DT_RowId = d[model.pk];
                  if (d.Total) {
                    d.Total = parseFloat(d.Total).toFixed(2);
                  }
                });

                $('#example_wrapper').css({"display": "block"});
                $('#spinner-container').css({"display": "none"});


                callback({
                  data: items,  // Don't sort - backend already sorted it
                  recordsTotal: total,
                  recordsFiltered: total
                });
           //
              },
            });


          },
        columns: [
          ...dt_columns,

            {
              data: "StatusQuotation",

              render: render.col_2,
            },
            {
              data: "DT_RowId",
              orderable: true,
              render: render.col_1,
            }
        ],
        columnDefs: [
          { targets: 0, type: 'date' },  // Apply built-in date sorting to the date column
          { targets: 1, type: 'number' },  // Apply built-in date sorting to the date column
          { targets: 2, type: 'text', visible: false},
      ],

        order: [
          // [0, 'desc'],
          // [1, 'desc']
        ],
      select: true,
      initComplete: function () {

        // Add custom search input
        $('.custom-search-container').html(`
          <div class="dataTables_filter" style="float: left; margin-bottom: 10px;">
            <label>
              <input type="search"
                     class="form-control form-control-sm"
                     id="customSearch"
                     placeholder="Type and press Enter to Search"
                     style="display: inline-block; width: 300px; font-size: 14px;" />
            </label>
          </div>
        `);

        initDlbClick();
        initEnter();

        // Для каждой колонки добавляем фильтр (input или select)
        this.api().columns().every(function (index) {
            var column = this;

            // Создаем фильтрующее поле в зависимости от типа данных колонки
            var filterCell = $('<th></th>').appendTo('.filter-row');
            if (index == 8) {
              var dropdownMenu = $('#status-dropdown .dropdown-menu');
              const dropdownButton = $('#status-dropdown button');

              dropdownMenu.empty();

              const statusValues = ['New', 'In Progress', 'Locked', 'Converted', 'Status Error'];
              const filterState = getFilterStateFromCookie('Statuses');

              if (statusValues.length > 0) {
                  dropdownButton.prop('disabled', false);
              } else {
                  dropdownButton.prop('disabled', true);
              }

              // Сначала добавляем статусы
              // Also build a complete state to sync cookie with current available values
              const syncedStatusState = [];
              statusValues.forEach(function (d) {
                  let isChecked;

                  if (filterState.length > 0) {
                      const savedState = filterState.find(item => item[d] !== undefined);
                      isChecked = savedState ? savedState[d] : true;
                  } else {
                      const isExcluded = d.includes('Converted') || d.includes('Deleted');
                      isChecked = isExcluded ? '' : 'checked';
                  }

                  // Add to synced state (includes new values that weren't in cookie)
                  syncedStatusState.push({ [d]: isChecked ? 1 : 0 });

                  dropdownMenu.append(
                      `<div class="form-check">
                          <input class="form-check-input st" type="checkbox"
                              ${isChecked ? 'checked' : ''} value="${d}" id="check_${d}">
                          <label class="form-check-label" for="check_${d}">${d}</label>
                      </div>`
                  );
              });

              // Sync cookie with all current status values
              saveFilterStateToCookie(syncedStatusState, 'Statuses');

              // Добавляем разделитель
              dropdownMenu.append('<hr class="dropdown-divider">');

              // Добавляем Select All
              dropdownMenu.append(
                  `<div class="form-check">
                      <input class="form-check-input" type="checkbox" id="selectAll">
                      <label class="form-check-label" for="selectAll">Select All</label>
                  </div>`
              );

              // Устанавливаем начальное состояние Select All
              const updateSelectAll = () => {
                  const totalCheckboxes = $('.form-check-input.st').length;
                  const checkedCheckboxes = $('.form-check-input.st:checked').length;
                  $('#selectAll').prop('checked', totalCheckboxes === checkedCheckboxes);
              };

              // Вызываем функцию при инициализации
              updateSelectAll();

              // Обработчик для Select All
              $('#selectAll').off('click').on('click', function() {
                  const isChecked = $(this).is(':checked');
                  dropdownMenu.find('.form-check-input.st').prop('checked', isChecked);

                  // Обновляем состояние фильтров и сохраняем в куки
                  const newState = [];
                  statusValues.forEach(value => {
                      const stateObj = {};
                      stateObj[value] = isChecked ? 1 : 0;
                      newState.push(stateObj);
                  });
                  saveFilterStateToCookie(newState, 'Statuses');

                  // Применяем фильтр
                  applyStatusFilter();
              });

              // Функция применения фильтра
              const applyStatusFilter = () => {
                  // With serverSide: true, we need to reload the table to trigger a new AJAX request
                  // The filter parameters are read from cookies in the ajax function
                  const tabl = $('#example').DataTable();
                  tabl.ajax.reload();
              };

              // Обработчик изменения отдельных чекбоксов
              dropdownMenu.on('change', '.form-check-input.st', function() {
                  const newState = getFilterStateFromCookie('Statuses');
                  const value = $(this).val();
                  const isChecked = $(this).is(':checked') ? 1 : 0;

                  updateFilterState(newState, value, isChecked);
                  saveFilterStateToCookie(newState, 'Statuses');

                  // Обновляем состояние Select All
                  updateSelectAll();

                  // Применяем фильтр
                  applyStatusFilter();
              });

              // Note: Removed initial applyStatusFilter() call - the DataTable's first AJAX request
              // already happened before initComplete, and subsequent reloads will read from UI checkboxes
          }
          else if (index == 7) {
            var dropdownMenu = $('#sales-rep-dropdown .dropdown-menu');
            const dropdownButton = $('#sales-rep-dropdown button');
            // Use unique sales reps from backend response instead of current page data
            let valuesRaw = window.uniqueSalesReps ? window.uniqueSalesReps : column.data().unique().sort();

            // Normalize to array and add helper methods for compatibility
            const valuesArray = Array.isArray(valuesRaw) ? valuesRaw : valuesRaw.toArray();
            const values = {
              data: valuesArray,
              length: valuesArray.length,
              each: function(callback) {
                this.data.forEach(callback);
              },
              toArray: function() {
                return this.data;
              }
            };

            dropdownMenu.empty();

            // Проверяем, есть ли только одно значение
            if (values.length === 1) {
                // Скрываем весь дропдаун
                $('#sales-rep-dropdown').hide();

                // Создаем скрытый стейт с отмеченным единственным значением
                const singleValue = values[0];
                const newState = [{[singleValue]: 1}];
                saveFilterStateToCookie(newState, 'salesRepFilterState');

                // Применяем фильтр с единственным значением
                applyFilter([singleValue], column);

                return; // Прерываем выполнение остального кода
            }

            // Если значений больше одного, показываем дропдаун
            $('#sales-rep-dropdown').show();
            dropdownButton.prop('disabled', values.length == 1);

            const filterState = getFilterStateFromCookie('salesRepFilterState');
            const selectedValues = [];

            // Добавляем sales rep чекбоксы
            // Also build a complete state to sync cookie with current available values
            const syncedState = [];
            values.each(function(d) {
                const savedState = filterState.find(item => item[d] !== undefined);
                const isChecked = savedState ? savedState[d] : true;

                if (isChecked) selectedValues.push(d);

                // Add to synced state (includes new values that weren't in cookie)
                syncedState.push({ [d]: isChecked ? 1 : 0 });

                dropdownMenu.append(
                    `<div class="form-check">
                        <input class="form-check-input sales-rep" type="checkbox"
                            ${isChecked ? 'checked' : ''} value="${d}" id="check_${d}">
                        <label class="form-check-label" for="check_${d}">${d}</label>
                    </div>`
                );
            });

            // Sync cookie with all current values (adds new sales reps that weren't in cookie)
            saveFilterStateToCookie(syncedState, 'salesRepFilterState');

            // Добавляем разделитель
            dropdownMenu.append('<hr class="dropdown-divider">');

            // Добавляем Select All
            dropdownMenu.append(
                `<div class="form-check">
                    <input class="form-check-input" type="checkbox" id="selectAllSalesRep">
                    <label class="form-check-label" for="selectAllSalesRep">Select All</label>
                </div>`
            );

            // Функция обновления состояния Select All
            const updateSelectAll = () => {
                const totalCheckboxes = $('.form-check-input.sales-rep').length;
                const checkedCheckboxes = $('.form-check-input.sales-rep:checked').length;
                $('#selectAllSalesRep').prop('checked', totalCheckboxes === checkedCheckboxes);
            };

            // Устанавливаем начальное состояние Select All
            updateSelectAll();

            // Обработчик для Select All
            $('#selectAllSalesRep').off('click').on('click', function() {
                const isChecked = $(this).is(':checked');
                dropdownMenu.find('.form-check-input.sales-rep').prop('checked', isChecked);

                // Обновляем состояние фильтров и сохраняем в куки
                const newState = [];
                values.each(function(value) {
                    const stateObj = {};
                    stateObj[value] = isChecked ? 1 : 0;
                    newState.push(stateObj);
                });
                saveFilterStateToCookie(newState, 'salesRepFilterState');

                // Собираем все отмеченные значения для фильтра
                const updatedValues = isChecked ? values.toArray() : [];
                applyFilter(updatedValues, column);
            });

            // Обработчик изменений в отдельных чекбоксах
            $('#sales-rep-dropdown').on('change', '.form-check-input.sales-rep', function() {
                const newState = getFilterStateFromCookie('salesRepFilterState');
                const value = $(this).val();
                const isChecked = $(this).is(':checked') ? 1 : 0;

                updateFilterState(newState, value, isChecked);
                saveFilterStateToCookie(newState, 'salesRepFilterState');

                // Обновляем состояние Select All
                updateSelectAll();

                // Собираем все отмеченные значения для фильтра
                const updatedValues = dropdownMenu.find('.form-check-input.sales-rep:checked')
                    .map(function() { return $(this).val(); }).get();

                applyFilter(updatedValues, column);
            });

            // Note: Removed initial applyFilter() call - we'll do ONE reload after all filters are built
        }

        });

        // After all filters are built and cookies are synced, do ONE reload to apply the correct filters
        // This ensures new sales reps/statuses are included in the query
        const tabl = $('#example').DataTable();
        tabl.ajax.reload(null, false);  // false = don't reset pagination

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

    },
    drawCallback: function() {
      // Auto-focus custom search field and move cursor to end after table redraw
      const searchInput = $('#customSearch');
      if (searchInput.length && searchInput.val()) {
        searchInput.focus();
        // Move cursor to end
        const val = searchInput.val();
        searchInput.val('').val(val);
      }
    }

    });

    // Handle Enter key press for search (using delegated event handler)
    // This is outside initComplete so it's only attached once
    $(document).off('keydown', '#customSearch').on('keydown', '#customSearch', function(e) {
      if (e.which === 13 || e.keyCode === 13) { // Enter key
        e.preventDefault();
        e.stopPropagation(); // Stop event from bubbling to global Enter handler
        e.stopImmediatePropagation(); // Ensure no other handlers run
        console.log('🔍 Search triggered with value:', $(this).val());
        table.ajax.reload();
        return false;
      }
    });

    $('.newQutation-button').html(`<a href="${newUrl}" class="btn btn-primary">New Quotation</a>`);
    $('.newQutation-button').on('click', function() {
      setCustomerInfo();
      window.location.href = newUrl;
      var state = table.state.loaded();
      if (state) {
          table.columns().every(function (index) {
              var colSearch = state.columns[index].search;
              if (colSearch.search) {
                  $('.filter-row th:eq(' + index + ') input, .filter-row th:eq(' + index + ') select')
                      .val(colSearch.search);
              }
          });
      }
  });

    $('#example')?.DataTable()?.on('length.dt', function(e, settings, len) {
    SetTableLenght(len)

});
}










function initDlbClick(){
  $(document).ready(function() {
    var table = $('#example').DataTable(); // Инициализация DataTable

    // Обработка двойного клика на строке
    $('#example tbody').on('dblclick', 'tr', function() {
        var clickedRow = $(this); // Текущая строка
        var actionLink = clickedRow.find('a:contains("Edit"), a:contains("View")'); // Поиск ссылок 'Edit' или 'View'

        if (actionLink.length > 0) {
            actionLink[0].click(); // Выполнение клика по первой найденной ссылке
        } else {
            console.log("Нет ссылки 'Edit' или 'View' в выделенной строке."); // Обработка случая, когда ссылки не найдены
        }
    });
});
}

function initEnter(){
  $(document).on('keydown', function(e) {
    if (e.which === 13) { // Проверка нажатия клавиши Enter
        var selectedRow = $('#example tbody tr.selected'); // Получение выделенной строки

        if (selectedRow.length > 0) {
            var actionLink = selectedRow.find('a:contains("Edit"), a:contains("View")'); // Поиск ссылок 'Edit' или 'View'

            if (actionLink.length > 0) {
                actionLink[0].click(); // Выполнение клика по первой найденной ссылке
            } else {
                console.log("Нет ссылки 'Edit' или 'View' в выделенной строке."); // Обработка случая, когда ссылки не найдены
            }
        } else {
            console.log("Нет выделенной строки."); // Обработка случая, когда строка не выделена
        }
    }
  });
}





// Функция для сохранения состояния фильтров в куки
function saveFilterStateToCookie(state,name) {
  setCookie(name, JSON.stringify(state)); // Сохраняем как JSON
}

// Функция для получения состояния фильтров из куки
function getFilterStateFromCookie(name) {
  const state = getCookie(name);
  return state ? JSON.parse(state) : []; // Возвращаем массив, если куки есть
}

// Функция для обновления или добавления состояния в массив
function updateFilterState(state, name, value) {
  const existingIndex = state.findIndex(item => item[name] !== undefined);
  if (existingIndex !== -1) {
      state[existingIndex][name] = value; // Перезаписываем значение
  } else {
      state.push({ [name]: value }); // Добавляем новое состояние
  }
}

function getFilterStateByName(state, name) {
  const lowerName = name.toLowerCase();
  return state.find(item => Object.keys(item)[0].toLowerCase() === lowerName);
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

  // Снимаем выделение со всех строк и выделяем только нужную
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
  // With serverSide: true, we need to reload the table to trigger a new AJAX request
  // The filter parameters are read from cookies in the ajax function
  const tabl = $('#example').DataTable();
  tabl.ajax.reload();
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