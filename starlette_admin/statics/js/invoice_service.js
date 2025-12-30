let _globalAccountNo = null


$(document).ready(function () {
  toastr.options = {
    closeButton: true,
    progressBar: true,
    positionClass: "toast-top-right",
    timeOut: "1000",
  };

  // We use this file not only for details page, but for Invoices List page as well.
  // This approach hides unused requests.
  if (window.isInvoiceDetailPage) {
    GetInvoice()
    GetInvoiceInfo()
  }
});

const emailModal = new bootstrap.Modal(document.getElementById('emailModal'))
let _emailPayload = {}

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

async function Print({ DBname, InvoiceID, InvoiceNumber, just_download = false }, rowindex = null) {
  const urlParams = new URLSearchParams(window.location.search)
  const q = {
    DBname: DBname || getCookie("DB"),
    InvoiceID: InvoiceID || urlParams.get("InvoiceID") || 0,
    InvoiceNumber: InvoiceNumber || urlParams.get("InvoiceNumber") || 0
  }

  return new Promise((resolve, reject) => {
    $.ajax({
      url: model.apiUrl + "/print_invoice",
      type: "POST",
      data: q,
      traditional: true,
      dataType: "json",
      success: function (response) {
        const pdfBase64 = response?.data_file_invoice?.[0]?.pdfFile

        if (!pdfBase64) {
          toastr.error("PDF not found in response.")
          reject("No PDF found")
          return
        }

        const fileName = `invoice_${InvoiceNumber}.pdf`
        const dataUri = "data:application/pdf;base64," + pdfBase64

        if (just_download) {
          const link = document.createElement("a")
          link.href = dataUri
          link.download = fileName
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
        } else {
          $('#pdfViewer').attr('src', dataUri)

          const modalPromise = new Promise((resolve) => {
            $('#printModal').on('shown.bs.modal', function () {
              resolve(response)
            })
          })

          let modal = new bootstrap.Modal(document.getElementById('printModal'))
          modal.show()

          let invoiceLabel = $('#invoiceLabel')
          if (invoiceLabel.length) {
            invoiceLabel.text(response?.data_file_quotation?.[0]?.status_quotation?.toString())
            invoiceLabel.removeClass('display-none')
          }

          if (rowindex !== undefined) {
            let table = $('#example').DataTable()
            table.row(rowindex).select()
            let row = table.row(rowindex)

            if (row.length > 0) {
              row.select().show().draw(false)

              $(row.node()).find(".btn-outline-danger").removeClass("btn-outline-danger").addClass("btn-danger")
              $(row.node()).find(".btn-outline-warning").removeClass("btn-outline-warning").addClass("btn-warning")
              $(row.node()).find(".btn-outline-info").removeClass("btn-outline-info").addClass("btn-info")
              $(row.node()).find(".btn-outline-success").removeClass("btn-outline-success").addClass("btn-success")
              $(row.node()).find(".btn-outline-secondary").removeClass("btn-outline-secondary").addClass("btn-secondary")
            }
          }
        }

        resolve(response)
      },
      error: function (xhr, status, error) {
        console.error(xhr.responseText)
        reject(error)
      }
    })
  })
}

function loadCustomerEmail(accountNo) {
  const db = getCookie("DB");
  if (!db) {
    toastr.error("Missing DB cookie");
    return;
  }

  const url = `/api/get_customer_email/${db}/${accountNo}/`;

  $.ajax({
    url: url,
    type: "GET",
    dataType: "json",
    success: function(res) {
      const email = res.email || "";
      $('#emailInput')
        .val(email)
        .toggleClass('is-invalid', email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email));
    },
    error: function(xhr, status, error) {
      toastr.error("Failed to load customer email");
      console.error("get_customer_email error:", xhr.responseText);
      $('#emailInput').val("").removeClass('is-invalid');
    }
  });
}

function SendEmail(arg) {
  let DBname, InvoiceID, InvoiceNumber;

  if (arg instanceof HTMLElement) {
    DBname        = arg.dataset.dbname;
    InvoiceID     = arg.dataset.invoiceId;
    InvoiceNumber = arg.dataset.invoiceNumber;
    AccountNo     = arg.dataset.AccountNo;

  } else if (arg && typeof arg === 'object' && (
    'DBname' in arg || 'InvoiceID' in arg || 'InvoiceNumber' in arg
    )) {
    DBname        = arg.DBname;
    InvoiceID     = arg.InvoiceID;
    InvoiceNumber = arg.InvoiceNumber;
    AccountNo     = arg.AccountNo;

  } else {
    const params = new URLSearchParams(window.location.search);
    DBname        = params.get("DBname");
    InvoiceID     = params.get("InvoiceID");
    InvoiceNumber = params.get("InvoiceNumber");
    AccountNo     = params.get("AccountNo");
  }

  DBname        = DBname || getCookie("DB");
  InvoiceID     = InvoiceID || $('#InvoiceID').val();
  InvoiceNumber = InvoiceNumber || $('#InvoiceNumber').val() || $('#qnumber').val();
  AccountNo = AccountNo || $('#AccountNo').val() || _globalAccountNo;

  _emailPayload = { DBname, InvoiceID, InvoiceNumber, AccountNo };

  $('#emailInput').val("").removeClass('is-invalid');

  const defaultBody =
    `Hello,\n\n` +
    `Please find attached your invoice #${InvoiceNumber}.\n\n` +
    `Thank you for your business.`;
  $('#bodyInput').val(defaultBody).removeClass('is-invalid');

  loadCustomerEmail(_emailPayload.AccountNo);
  emailModal.show();
  $('#bodyInput').on('keydown', function(e){
    // To avoid usage of global handler by Enter/Shift+Enter.
    e.stopPropagation();
  });
}

$('#emailForm').on('submit', function(e) {
  e.preventDefault();

  const email     = $('#emailInput').val().trim();
  const body      = $('#bodyInput').val().trim();
  let   valid     = true;

  if (!email) {
    $('#emailInput').addClass('is-invalid');
    valid = false;
  } else {
    $('#emailInput').removeClass('is-invalid');
  }

  if (!body) {
    $('#bodyInput').addClass('is-invalid');
    valid = false;
  } else {
    $('#bodyInput').removeClass('is-invalid');
  }

  if (!valid) return;

  const payload = {
    DBname: _emailPayload.DBname,
    InvoiceID: _emailPayload.InvoiceID,
    InvoiceNumber: _emailPayload.InvoiceNumber,
    Email: email,
    body: body
  };

  $.ajax({
    url: model.apiUrl + "/send_email",
    type: "POST",
    data: payload,
    dataType: "json",
    success(response) {
      if (response.error === 0) {
        toastr.success("Invoice sent to " + email);
      } else {
        toastr.error("Failed to send email: " + response.error_info);
      }
      emailModal.hide();
    },
    error() {
      toastr.error("Error sending email.");
      emailModal.hide();
    }
  });
});

async function PrintInvoice(arg) {
  let InvoiceID, InvoiceNumber, just_download = false;

  if (arg instanceof HTMLElement) {
    InvoiceID = arg.dataset.invoiceId;
    InvoiceNumber = arg.dataset.invoiceNumber;
    just_download = arg.dataset.justDownload === "true";
  } else if (typeof arg === 'object') {
    InvoiceID = arg.InvoiceID;
    InvoiceNumber = arg.InvoiceNumber;
    just_download = arg.just_download || false;
  }

  InvoiceID = InvoiceID || $('#InvoiceID').val();
  InvoiceNumber = InvoiceNumber || $('#qnumber').val();
  let modelDop = sessionStorage.getItem('modelDop');

  const payload = {
    modelDop,
    InvoiceID,
    InvoiceNumber,
    just_download
  };

  await Print(payload);
}

async function GetInvoice() {
  try {
    let queryParams = new URLSearchParams(window.location.search).toString();
    if (!queryParams) return;

    $(".dataTables_empty").text("Loading Invoice...");

    let data = await RequestInvoice(queryParams);
    if (!data || data.length === 0) {
      toastr.warning("No invoice data found.");
      return;
    }

    if (!$.fn.DataTable.isDataTable("#items-table")) {
      initInvoicesTable();
    }

    PopulateInvoiceDetails(data);
    $("#items-table").show();
  } catch (error) {
    toastr.error(error?.responseText || "Error loading invoice.");
  }
}

async function RequestInvoice(queryParams) {
  try {
    const response = await $.ajax({
      url: model.apiUrl + "/view_invoice?" + queryParams,
      type: "GET",
      dataType: "json",
    });
    return response;
  } catch (error) {
    toastr.error("Error retrieving invoice data.");
  }
}

function CloseInvoice(link = null) {
  $('#quotationForm').addClass('modal-blur-bg');
  setTimeout(async () => {
    let href;
    if (link) {
      href = link;
    } else {
      href = model.apiUrl.replace('api1/InvoicesDetails_tbl', 'invoices2_tbl');
    }
    window.location.href = href;
  }, 100);
}

async function GetInvoiceInfo() {
  try {
    let urlParams = new URLSearchParams(window.location.search);
    let dbName = urlParams.get("DBname");
    let invoiceID = urlParams.get("InvoiceID");

    if (!dbName || !invoiceID) {
      toastr.error("Missing required query parameters.");
      return;
    }

    let response = await $.ajax({
      url: `/api/get_invoice_info/`,
      type: "GET",
      dataType: "json",
      data: { db: dbName, invoice_id: invoiceID },
    });
    if (response && typeof response === "object") {
      RenderInvoiceDetails(response);

      _globalAccountNo = response.AccountNo || null
    } else {
      toastr.warning("No invoice information found.");
    }
  } catch (error) {
    console.error("Invoice API Error:", error);
    toastr.error("Error retrieving invoice details.");
  }
}

function RenderInvoiceDetails(invoice) {
  $("#invoice-number").text(invoice.InvoiceNumber || "-");
  $("#invoice-date").text(invoice.InvoiceDate ? formatDate(invoice.InvoiceDate) : "-");
  $("#business-name").text(invoice.BusinessName || "-");
  $("#account-number").text(invoice.AccountNo || "-");
  $("#sales-rep").text(invoice.FirstName || "-");
  $("#notes").text(invoice.Notes || "-");
}

function formatDate(dateStr) {
  let date = new Date(dateStr);
  return date.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "2-digit" });
}

function PopulateInvoiceDetails(data) {
  let table = $("#items-table").DataTable();

  let totalItems = data.length;
  let totalQuantity = 0;
  let totalCost = 0;
  let totalPrice = 0;

  let formattedData = data.map(item => {
    let qtyShipped = item.QtyShipped || 0;
    let unitPrice = item.UnitPrice ? parseFloat(item.UnitPrice) : 0;
    let unitCost = item.UnitCost ? parseFloat(item.UnitCost) : 0;
    let extendedPrice = item.ExtendedPrice ? parseFloat(item.ExtendedPrice) : 0;

    totalQuantity += qtyShipped;
    totalCost += unitCost * qtyShipped;
    totalPrice += extendedPrice;

    return {
      QtyShipped: qtyShipped,
      ProductDescription: item.ProductDescription || "No description",
      UnitPrice: `$${unitPrice.toFixed(2)}`,
      UnitCost: `$${unitCost.toFixed(2)}`,
      ExtendedPrice: `$${extendedPrice.toFixed(2)}`,
    };
  });

  table.clear().rows.add(formattedData).draw();
  UpdateInvoiceTotals(totalItems, totalQuantity, totalCost, totalPrice);
}

function UpdateInvoiceTotals(totalItems, totalQuantity, totalCost, totalPrice) {
  $("#totalitems strong").text(totalItems);
  $("#totalqty strong").text(totalQuantity);
  $("#totalcost strong").text(`$${totalCost.toFixed(2)}`);
  $("#totalprice strong").text(`$${totalPrice.toFixed(2)}`);
}

function initInvoicesTable() {
  $("#items-table").DataTable({
    dom: "rtS",
    scrollY: "60vh",
    scrollCollapse: true,
    paging: false,
    searching: false,
    info: false,
    fixedHeader: true,
    ordering: false,
    columns: [
      { data: "QtyShipped", title: "Quantity Shipped", className: "text-center" },
      { data: "ProductDescription", title: "Product Description", className: "text-left" },
      { data: "UnitPrice", title: "Unit Price", className: "text-right" },
      { data: "UnitCost", title: "Unit Cost", className: "text-right" },
      { data: "ExtendedPrice", title: "Total", className: "text-right" },
    ],
    columnDefs: [
      { targets: [0], width: "5%" },
      { targets: [2, 3, 4], width: "15%" },
      { targets: [1], width: "35%" },
    ],
  });
}
