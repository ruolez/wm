function GetQuickSearchItem(StockRequested =1) {
    let searchById = $("#quickSearchButton").attr("data-id");
    let searchBy = $("#quickSearchButton").val();
    let searchValue = $("#quicksearch").val();

    if (!searchById || !searchBy || !searchValue) {
      return Promise.reject("some value is empty");
    }

    let searchData = {
      DB: GetDb(),
      searchById: searchById,
      searchBy: searchBy,
      searchValue: searchValue,
      anum: $("#acnumInput").val()||"",
      isStockRequested:StockRequested
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

  function RedirectToList(navigateTo){
    let targetNavLink = $('.nav-link').find('.nav-link-title').filter(function() {
      return $(this).text().trim() === navigateTo;
    }).closest('.nav-link');
    var href = targetNavLink.attr('href');

    window.location.href = href;
  }

