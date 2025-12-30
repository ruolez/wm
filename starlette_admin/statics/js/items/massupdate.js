let selectedModelId = GetDb();

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
  setDropdownFromCookie();
});



function GenerateData() {
  return {
    data: [],
  };
}

function InitDataTable() {
  BrowseItems().catch(function (error) {
    toastr.error("Error:", error);
  });
}

$(document).ready(function () {
  $("#lookinDropdown")
    .next(".dropdown-menu")
    .on("click", ".dropdown-item", function () {
      InitDataTable();
    });
});

function BrowseItems() {
  return new Promise(function (resolve, reject) {
    CleanDatable("#items-table");
    var table = new DataTable("#items-table", {
      dom: '<"massUpdate-button"> <"top"f<"clear">>rt <"info">i ',
      scrollY: true,
      paging: false,
      lengthChange: false,
      searching: false,
      info: true,
      colReorder: false,
      info: false,
      select: {
        style: 'multi'
    },
      ajax: function (data, callback, settings) {
        let inputValue = $("#modalsearch").val();

        if (inputValue?.length > 2) {
          GetBrowseItems(ReplaceSpace(inputValue))
            .then(function (response) {
              MassUpadateButtonVisability(response.data.length);
              let modifiedResponse = response;
              callback(modifiedResponse);
              resolve();
            })
            .catch(function (error) {
              console.error("Error fetching data:", error);
              reject(error);
            });
        } else {
          callback(GenerateData());
        }
      },
      columns: [
        { data: "Description" },
        { data: "SKU" },
        { data: "UPC" },
        {
          data: "UnitPrice",
          render: function (data, type, row) {
            return parseFloat(data).toFixed(2);
          },
        },
        {
          data: "UnitCost",
          render: function (data, type, row) {
            return parseFloat(data).toFixed(2);
          },
        },
        {
          data: "DeliveryB",
          render: function (data, type, row) {
            return parseFloat(data).toFixed(2);
          },
        },
        {
          data: "Discontinued",
          orderable: false,
          className: "td-wrapper",
          render: function (data, type, row) {
            if (type === "display") {
              return `<input type="checkbox" class="form-check-input" ${
                data ? "checked" : ""
              } style="pointer-events: none;">`;
            }
            return data;
          },
        },
      ],
      columnDefs: [
        {
          target: 0,
          visible: true,
          width: "38%",
        },
        {
          target: 1,
          visible: true,
          width: "15%",
        },
        {
          target: 2,
          visible: true,
          width: "15%",
        },
        {
          target: 3,
          visible: true,
          width: "10%",
        },
        {
          target: 4,
          visible: true,
          width: "10%",
        },
        {
          target: 5,
          visible: true,
          width: "10%",
        },
        {
          target: 6,
          visible: true,
          width: "15%",
        },
      ],
    });

    InitMassUpdateButton();
  });
}

$(document).ready(function () {
  $('#massUpdateModal input[type="number"]').on("change", function () {
    var value = parseFloat($(this).val());
    var formattedValue = value.toFixed(2);
    $(this).val(formattedValue);
  });
});



function InitMassUpdateButton() {
  let svgIcon =
    '<svg xmlns="http://www.w3.org/2000/svg"  width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-edit"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M7 7h-1a2 2 0 0 0 -2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2 -2v-1" /><path d="M20.385 6.585a2.1 2.1 0 0 0 -2.97 -2.97l-8.415 8.385v3h3l8.385 -8.415z" /><path d="M16 5l3 3" /></svg>';

  let massUpdateButton = $(document.createElement("button"))
    .attr("id", "massUpdate-button")
    .addClass("btn btn-primary mb-2")
    .prop("disabled", true)
    .html(svgIcon + "Update");
  $(".massUpdate-button").replaceWith(massUpdateButton);
  //using session storage for select box 'chouse db'

  $("#massUpdate-button").on("click", function () {
    $("#unitcost").val("");
    $("#unitprice").val("");
    $("#deliveryb").val("");
    $("#massUpdateModal").modal("show");
  });
}

function MassUpadateButtonVisability(length) {
  if (length > 0) {
    $("#massUpdate-button")?.prop("disabled", false);

  } else {
    $("#massUpdate-button")?.prop("disabled", true);
  }
}

$(document).ready(function () {
  InitDataTable();
  document.getElementById("modalsearch").focus();
});

$("#modalsearch").on("click", function () {
  if ($(this).val()) {
    $(this).select();
  }
});

$("#modalsearch").on(
  "input",
  Debounce(function () {
    InitDataTable();
  }, 300)
);

$("#saveNewPrices").click(function () {
 let items= UpdateValues();
 if (items?.length > 0) {
  SendUpdatedItems(items);
}
});

function UpdateValues() {

  let items = $("#items-table").DataTable().rows({ selected: true }).data().toArray();

  if (items?.length<=0)
  {
    items = $("#items-table").DataTable().rows().data().toArray();
  }

  let unitcostvalue = parseFloat($("#unitcost").val());
  let unitpricevalue = parseFloat($("#unitprice").val());
  let deliverybvalue = parseFloat($("#deliveryb").val());
  let unitcost;
  let unitprice;
  let deliveryb;

  if (!isNaN(unitcostvalue) && unitcostvalue >= 0) {
    unitcost = unitcostvalue;
  }

  if (!isNaN(unitpricevalue) && unitpricevalue >= 0) {
    unitprice = unitpricevalue;
  }

  if (!isNaN(deliverybvalue) && deliverybvalue >= 0) {
    deliveryb = deliverybvalue;
  }

  for (var i = 0; i < items.length; i++) {
    items[i].UnitCost = unitcost ?? items[i].UnitCost;
    items[i].UnitPrice = unitprice ?? items[i].UnitPrice;
    items[i].DeliveryB = deliveryb ?? items[i].DeliveryB;
  }
 return items;

}


