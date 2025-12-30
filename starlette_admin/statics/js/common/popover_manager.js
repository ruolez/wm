class PopoverManager {
    constructor() {
      if (PopoverManager.instance) {
        return PopoverManager.instance;
      }
  
      this.isPopoverActive = false;
      PopoverManager.instance = this;
    }
  
    showPopover(element, row, unitprice, classlist) {
      // Проверка, активен ли уже popover
      if (this.isPopoverActive) return;
  
      this.isPopoverActive = true;
  
      const form = document.getElementById("exampleModal");
      form.classList.add("disable-clicks");
  
      let overlay = document.createElement('div');
      overlay.classList.add('form-overlay');
      form.appendChild(overlay);
  
      $(element).popover('dispose');
      $(element).popover({
        html: true,
        id: 'popvb',
        content: function() {
          return `<div class="popover-body p-0 text-center">
                    <a href="#" class="btn btn-secondary btn-sm" id="YesRemember">Yes</a>
                    <a href="#" class="btn btn-secondary btn-sm" id="NoRemember">No</a>
                  </div>`;
        },
        title: `<div p-0 text-center>Remember price?</div>`,
        placement: 'top',
        trigger: 'manual'
      }).popover('show');
  
      // Восстановление состояния документа и popover
      const restoreDocumentState = () => {
        form.classList.remove("disable-clicks");
        overlay.remove();
        $(element).popover('dispose');
        this.isPopoverActive = false;
        $(document).off("click", "#YesRemember");
        $(document).off("click", "#NoRemember");
        $(document).off("keydown", handleKeyPress);
      };
  
      // Обработка кликов по "Yes" и "No"
      $(document).on("click", "#YesRemember", () => {
        row.data().rememberprice = 1;
        if (unitprice) {
          classlist.remove('unsetbackground');
          unitprice.childNodes[0].style.backgroundColor = 'var(--tblr-highlight-bg)';
        }
        UpdateItems(null, row, null);
        restoreDocumentState();
      });
  
      $(document).on("click", "#NoRemember", () => {
        row.data().rememberprice = 0;
        if (unitprice) {
          unitprice.childNodes[0].style.backgroundColor = '';
          classlist.add('unsetbackground');
          classlist.add('black-text-color')
        }
        UpdateItems(null, row, null);
        restoreDocumentState();
      });
  
      // Обработка нажатий на клавиши 'y' и 'n'
      const handleKeyPress = (event) => {
        if (event.key === "y") {
          $("#YesRemember").trigger("click");
        } else if (event.key === "n") {
          $("#NoRemember").trigger("click");
        }
      };
  
      $(document).on("keydown", handleKeyPress);
    }
  }