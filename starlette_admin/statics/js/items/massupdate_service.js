async function GetBrowseItems(inputValue) {
    let lookinValue = GetDropdownValue("#lookinDropdown");
    let searchData = {
      DB: GetDb(),
      searchValue: inputValue,
    };

    searchData = Object.assign({}, searchData, lookinValue);

    try {
      let response = await $.ajax({
        url: model.apiUrl + "/getitemsmassupdate",
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
            let dropdownMenu = $("#dropdownMenu");
            dropdownMenu.empty();
            db_list.forEach(function (item) {
              let dropdownItem = $("<a>").addClass("dropdown-item");
              dropdownItem.text(item.SourceDB).attr("data-value", item.id);

              dropdownItem.on("click", function (event) {
                $("#dropdownMenu .active").removeClass("active");
                $("#dropdownMenuButton").text(item.SourceDB);

                SetDb(item.id);
                $("#modalsearch").attr("disabled", false);
                $("#lookinDropdown").attr("disabled", false);

                if (item.id == GetDb()) {
                  $("#dropdownMenuButton")
                    .text(item.SourceDB)
                    .attr("data-value", item.id);
                  dropdownItem.addClass("active");
                }
                InitDataTable();
              });
              if (item.id == GetDb()) {
                $("#dropdownMenuButton")
                  .text(item.SourceDB)
                  .attr("data-value", item.id);
                dropdownItem.addClass("active");
              }
              dropdownMenu.append(dropdownItem);
            });
          }
          if (db_list.length > 1) {
            $("#dbDropdown").css("display", "block");
          } else {

            SetDb(db_list[0].id);
          }

          if (GetDb()) {
            $("#modalsearch").attr("disabled", false);
            $("#lookinDropdown").attr("disabled", false);
            $('#modalsearch')?.focus();
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


  async function SendUpdatedItems(items) {
    let DBname = GetDb();

    let paramsObj = {
      DBname: DBname,
      items: JSON.stringify(items),
    };

    try {
      await $.ajax({
        url: model.apiUrl + "/items_massupdate",
        type: "POST",
        data: paramsObj,
      });
      toastr.success("Success");
      InitDataTable();
      $("#massUpdateModal")?.modal("hide");
    } catch (error) {
      toastr.error("An error occurred while saving items");
    }
  }