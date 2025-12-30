$(function() {
  let currentUserName = null;

  const $rangeSelect = $('#activeRange');
  const $saveBtn = $('#saveSettingsBtn');
  const $accountsList = $('#accountsList');
  const $saveAccountsBtn = $('#saveAccountsBtn');
  const $syncAllBtn = $('#syncAllBtn');
  const $stopAllBtn = $('#stopAllBtn');
  const ALLOWED_MONTHS = [1, 2, 3, 4, 5, 6, 9, 12, 24, 36, 48, 60];

  toastr.options = {
    closeButton: true,
    progressBar: true,
    positionClass: 'toast-top-right',
    timeOut: '1000'
  };

  ALLOWED_MONTHS.forEach(m => {
    const label = `${m} month${m > 1 ? 's' : ''}`;
    $rangeSelect.append(`<option value="${m}">${label}</option>`);
  });

  $.getJSON('/api/get_time_range/')
    .done(data => {
      const cur = data.months;
      if (ALLOWED_MONTHS.includes(cur)) {
        $rangeSelect.val(cur);
      } else {
        toastr.warning('Unexpected time range received');
      }
    })
    .fail(() => {
      toastr.error('Error loading current time range');
    });

  function fetchSessionInfo() {
    return $.getJSON('/api/get_session_info/');
  }

  function loadAccounts() {
    if (!currentUserName) {
      toastr.error('Session not initialized');
      return;
    }

    $accountsList.empty();

    $.ajax({
      url: '/api/get_user_accounts/',
      method: 'GET',
      dataType: 'json',
      headers: { 'X-User-Name': currentUserName }
    })
    .done(data => {
      const accounts = Array.isArray(data.accounts) ? data.accounts : [];
      if (accounts.length === 0) {
        $accountsList.append(
          '<div class="alert alert-info">No linked accounts available.</div>'
        );
        $saveAccountsBtn.hide();
        return;
      }
      $saveAccountsBtn.show();

      accounts.forEach(acc => {
        const checked = acc.syncEnabled ? 'checked' : '';
        $accountsList.append(
          `<div class="form-check d-flex align-items-center mb-2">
             <input class="form-check-input" type="checkbox" value="${acc.id}" id="account_${acc.id}" ${checked}>
             <span class="badge rounded-pill mx-2" style="background-color:#206bc4;">${acc.db}</span>
             <label class="form-check-label mb-0" for="account_${acc.id}">${acc.username}</label>
           </div>`
        );
      });
    })
    .fail(() => {
      $accountsList.html(
        '<div class="alert alert-danger">Failed to load linked accounts.</div>'
      );
      toastr.error('Error loading linked accounts');
    });
  }

  function loadUserAccessMenu() {
    if (!currentUserName) {
      toastr.error('Session not initialized');
      return;
    }

    $.ajax({
      url: '/api/get_user_access_menu/' + currentUserName,
      type: 'GET',
      dataType: 'json',
      success: function(response) {
        const menuArray = Array.isArray(response.access_menu) ? response.access_menu : [];
        const $select = $('#userAccessMenu');

        $select.empty();
        $select.append('<option disabled selected value="">Select an item</option>');

        if (menuArray.length === 0) {
          $select.append('<option disabled value="">No menu items available</option>');
          return;
        }

        menuArray.forEach(item => {
          const displayText = item
            .toLowerCase()
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
          const valueText = item;

          $select.append(
            `<option value="${valueText}">${displayText}</option>`
          );
        });

        $.getJSON('/api/get_default_home_page/' + currentUserName)
          .done(data => {
            const currentHome = data.default_home_page;
            if (currentHome !== null && menuArray.includes(currentHome)) {
              $select.val(currentHome);
            } else {
              $select.val('');
            }
          })
          .fail(() => {
            $select.val('');
          });
      },
      error: function(xhr) {
        toastr.error('Failed to load access menu');
        console.error('get_user_access_menu error:', xhr.responseText);

        $('#userAccessMenu')
          .empty()
          .append('<option disabled selected>Error loading menu</option>');
      }
    });
  }

  fetchSessionInfo()
    .done(data => {
      if (data.username) {
        currentUserName = data.username;

        loadUserAccessMenu();

        $.getJSON(`/api/get_user_role/${currentUserName}`)
          .done(res => {
            const roles = Array.isArray(res.roles) ? res.roles.flat() : [];
            if (roles.includes('admin')) {
              $('[data-admin]').show();
            }
          })
          .fail(() => {
            toastr.error('Failed to fetch user role');
          })
          .always(loadAccounts);
      } else {
        toastr.error('Failed to retrieve session information');
      }
    })
    .fail(() => {
      toastr.error('Error fetching session information');
    });

  $saveBtn.on('click', () => {
    const sel = parseInt($rangeSelect.val(), 10);
    if (!ALLOWED_MONTHS.includes(sel)) {
      toastr.warning('Invalid selection');
      return;
    }
    $.ajax({
      url: '/api/set_time_range/',
      method: 'POST',
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify({ months: sel })
    })
    .done(res => {
      if (res.months === sel) {
        toastr.success(`Time range updated to ${sel} months`);
      } else {
        toastr.error(res.error || 'Unexpected response');
      }
    })
    .fail(() => {
      toastr.error('Failed to update time range');
    });
  });

  $saveAccountsBtn.on('click', e => {
    e.preventDefault();
    if (!currentUserName) {
      toastr.error('Session not initialized');
      return;
    }
    const ids = $accountsList.find('input:checked').map(function() {
      return Number(this.value);
    }).get();

    $.ajax({
      url: '/api/set_sync_accounts/',
      method: 'POST',
      contentType: 'application/json',
      dataType: 'json',
      headers: { 'X-User-Name': currentUserName },
      data: JSON.stringify({ accountIds: ids })
    })
    .done(res => {
      if (res.success) {
        toastr.success('Synchronization settings updated');
      } else {
        toastr.error(res.error || 'Unexpected server response');
      }
    })
    .fail(() => {
      toastr.error('Failed to update synchronization settings');
    });
  });

  $syncAllBtn.on('click', () => {
    if (!currentUserName) {
      toastr.error('Session not initialized');
      return;
    }
    $.post({
      url: '/api/admin/sync_all_accounts/',
      headers: { 'X-User-Name': currentUserName }
    })
    .done(res => {
      if (res.synced_pairs) {
        toastr.success('All accounts have been re-synced');
        loadAccounts();
      } else {
        toastr.error(res.error || 'Sync-all failed');
      }
    })
    .fail(() => {
      toastr.error('Failed to sync all accounts');
    });
  });

  $stopAllBtn.on('click', () => {
    if (!currentUserName) {
      toastr.error('Session not initialized');
      return;
    }
    $.post({
      url: '/api/admin/stop_all_sync/',
      headers: { 'X-User-Name': currentUserName }
    })
    .done(res => {
      if (res.stopped_count !== undefined) {
        toastr.success('All synchronization stopped');
        loadAccounts();
      } else {
        toastr.error(res.error || 'Stop-all failed');
      }
    })
    .fail(() => {
      toastr.error('Failed to stop all synchronization');
    });
  });

  $('#saveHomePageBtn').on('click', () => {
    if (!currentUserName) {
      toastr.error('Session not initialized');
      return;
    }
    const selectedHome = $('#userAccessMenu').val() || null;

    $.ajax({
      url: '/api/set_default_home_page/' + currentUserName,
      type: 'POST',
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify({ default_home_page: selectedHome }),
      success(response) {
        if (response.error) {
          toastr.error(`Error: ${response.error}`);
        } else {
          toastr.success('Default home page updated');
        }
      },
      error(xhr) {
        const err = xhr.responseJSON?.error || 'Failed to update default home page';
        toastr.error(err);
      }
    });
  });

  $('#removeHomePageBtn').on('click', () => {
    if (!currentUserName) {
      toastr.error('Session not initialized');
      return;
    }

    $.ajax({
      url: '/api/set_default_home_page/' + currentUserName,
      type: 'POST',
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify({ default_home_page: null }),
      success(response) {
        if (response.error) {
          toastr.error(`Error: ${response.error}`);
        } else {
          $('#userAccessMenu').val('');
          toastr.success('Default home page removed');
        }
      },
      error(xhr) {
        const err = xhr.responseJSON?.error || 'Failed to remove default home page';
        toastr.error(err);
      }
    });
  });
});
