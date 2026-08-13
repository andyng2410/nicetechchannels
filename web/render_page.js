(() => {
  const MAX_AUDIO_BYTES = 200 * 1024 * 1024;
  const MAX_RENDER_VIDEO_BYTES = 200 * 1024 * 1024;
  const MAX_BRAND_LOGO_BYTES = 20 * 1024 * 1024;
  const fallbackProject = window.__RENDER_PROJECT__;
  const fallbackOutputUrl = window.__RENDER_OUTPUT_URL__;
  const projects = Array.isArray(window.__PROJECTS__) && window.__PROJECTS__.length
    ? window.__PROJECTS__
    : (fallbackProject ? [{ name: fallbackProject, url: `/slide/${fallbackProject}/`, output_url: fallbackOutputUrl, video_url: fallbackOutputUrl, script_count: 0 }] : []);
  const projectMap = new Map(projects.map((project) => [project.name, project]));
  const state = {
    engine: 'elevenlabs',
    jobId: null,
    pollTimer: null,
    project: null,
    outputUrl: null,
    busy: false,
    canceling: false,
    uploadProject: null,
    socialReady: { youtube: false, facebook: false },
    facebookCommentTargetId: '',
    facebookActivePageId: '',
    renderOptions: {
      outroFile: null,
      brandLogoFile: null,
      brandName: '@nicetechchannels',
    },
  };
  let elevenVoiceSaveTimer = null;
  let elevenVoiceSaving = false;
  let elevenApiKeySaveTimer = null;
  let elevenApiKeySaving = false;
  let facebookConfigSaving = false;

  function $(selector) {
    return document.querySelector(selector);
  }

  function $all(selector) {
    return Array.from(document.querySelectorAll(selector));
  }

  function setButtonLabel(button, label) {
    const labelEl = button?.querySelector?.('span:last-child');
    if (labelEl) labelEl.textContent = label;
    else if (button) button.textContent = label;
  }

  function applyTheme(theme) {
    const nextTheme = theme === 'light' ? 'light' : 'dark';
    document.body.classList.toggle('theme-light', nextTheme === 'light');
    localStorage.setItem('nicetechchannels-theme', nextTheme);
    $all('[data-theme-toggle]').forEach((button) => {
      const icon = button.querySelector('.btn-icon');
      const label = button.querySelector('span:last-child');
      if (icon) icon.textContent = nextTheme === 'light' ? '☀' : '☾';
      if (label) label.textContent = nextTheme === 'light' ? 'Light' : 'Dark';
    });
  }

  function toggleTheme() {
    applyTheme(document.body.classList.contains('theme-light') ? 'dark' : 'light');
  }

  function currentProject() {
    return projectMap.get(state.project) || null;
  }

  function rowForProject(projectName) {
    return $all('.project-row[data-project]').find((element) => element.dataset.project === projectName) || null;
  }

  function setStatus(message, tone = 'warn') {
    const status = $('#renderStatus');
    if (!status) return;
    status.textContent = message;
    status.hidden = !message;
    status.className = `status ${tone}`;
  }

  function reloadWithSourceProjects(data) {
    const nextProjects = Array.isArray(data?.projects) ? data.projects : [];
    const url = new URL(window.location.href);
    const firstProject = nextProjects[0]?.name || '';
    if (firstProject) url.searchParams.set('project', firstProject);
    else url.searchParams.delete('project');
    window.location.href = `${url.pathname}${url.search}`;
  }

  function setSourceSelectStatus(message, tone = 'warn') {
    if ($('#renderStatus')) {
      setStatus(message, tone);
    } else if ($('#uploadStatus')) {
      setUploadStatus(message, tone);
    }
  }

  async function selectSourceRootFromFinder() {
    const buttons = $all('[data-source-root-select]');
    buttons.forEach((button) => { button.disabled = true; });
    setSourceSelectStatus('Đang mở Finder để chọn source folder...', 'warn');
    try {
      const response = await fetch('/api/source-root/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      const count = Array.isArray(data.projects) ? data.projects.length : 0;
      setSourceSelectStatus(`Đã đổi source. Tìm thấy ${count} project.`, 'good');
      window.setTimeout(() => reloadWithSourceProjects(data), 250);
    } catch (error) {
      setSourceSelectStatus(error.message || String(error), 'bad');
    } finally {
      buttons.forEach((button) => { button.disabled = false; });
    }
  }

  function setRevealOutputButton(projectName = state.project, visible = false) {
    const button = $('#revealOutput');
    if (!button) return;
    button.dataset.project = projectName || '';
    button.hidden = !visible;
    button.disabled = false;
  }

  function setUploadCenterLink(projectName = state.project, visible = false) {
    const link = $('#uploadCenterLink');
    if (!link) return;
    link.href = projectName ? `/upload?project=${encodeURIComponent(projectName)}` : '/upload';
    link.hidden = !visible;
  }

  function setUploadEmpty(projectName = state.project, visible = false) {
    const empty = $('#uploadEmpty');
    if (!empty) return;
    const title = $('#uploadEmptyProject');
    if (title) title.textContent = projectName ? `${projectName} chưa có final_video.mp4` : 'Project này chưa có final_video.mp4';
    empty.hidden = !visible;
  }

  function setProjectVideoBadge(project) {
    const badge = $('#projectVideoBadge');
    if (!badge) return;
    const ready = Boolean(project?.video_url);
    badge.textContent = ready ? 'có final_video' : 'chưa render';
    badge.className = `project-video-badge ${ready ? 'ready' : 'missing'}`;
  }

  function setUploadStatus(message = '', tone = 'warn') {
    const status = $('#uploadStatus');
    if (!status) return;
    status.textContent = message;
    status.hidden = !message;
    status.className = `upload-status ${tone}`;
  }

  function setUploadResult(message = '', tone = 'warn', links = []) {
    const result = $('#uploadResult');
    if (!result) return;
    result.textContent = '';
    result.hidden = !message && !links.length;
    result.className = `upload-result ${tone}`;
    if (message) {
      const text = document.createElement('span');
      text.textContent = message;
      result.appendChild(text);
    }
    links.forEach((link) => {
      result.appendChild(document.createTextNode(' '));
      const anchor = document.createElement('a');
      anchor.href = link.href;
      anchor.target = '_blank';
      anchor.rel = 'noreferrer';
      anchor.textContent = link.label;
      result.appendChild(anchor);
    });
  }

  function waitMs(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, Math.max(0, Number(ms) || 0)));
  }

  async function commentFacebookSourceWithDelay(project, facebookUploadedAt) {
    const firstDelay = 30000;
    const retryDelay = 45000;
    const elapsed = Date.now() - Number(facebookUploadedAt || 0);
    const waitBeforeFirstTry = Math.max(0, firstDelay - elapsed);
    if (waitBeforeFirstTry > 0) {
      setUploadStatus(`YouTube xong. Chờ ${Math.ceil(waitBeforeFirstTry / 1000)} giây để Facebook tạo object rồi comment nguồn...`, 'warn');
      await waitMs(waitBeforeFirstTry);
    }
    try {
      setUploadStatus('Đang comment nguồn lên Facebook...', 'warn');
      return await commentFacebookSource(project);
    } catch (firstError) {
      setUploadStatus(`Comment nguồn chưa được. Chờ ${Math.ceil(retryDelay / 1000)} giây rồi thử lại...`, 'warn');
      await waitMs(retryDelay);
      try {
        setUploadStatus('Đang thử comment nguồn lên Facebook lần 2...', 'warn');
        return await commentFacebookSource(project);
      } catch (secondError) {
        secondError.message = `${secondError.message || String(secondError)}. Lần thử đầu cũng lỗi: ${firstError.message || String(firstError)}`;
        throw secondError;
      }
    }
  }

  function flashCopyButton(button) {
    if (!button) return;
    const icon = button.querySelector('.btn-icon');
    if (!icon) return;
    if (!button.dataset.defaultIcon) button.dataset.defaultIcon = icon.textContent || '⧉';
    if (!button.dataset.defaultTitle) button.dataset.defaultTitle = button.getAttribute('title') || 'Copy';
    if (!button.dataset.defaultAriaLabel) button.dataset.defaultAriaLabel = button.getAttribute('aria-label') || button.dataset.defaultTitle;
    icon.textContent = '✓';
    button.setAttribute('title', 'Đã copy');
    button.setAttribute('aria-label', 'Đã copy');
    if (button._copyResetTimer) window.clearTimeout(button._copyResetTimer);
    button._copyResetTimer = window.setTimeout(() => {
      icon.textContent = button.dataset.defaultIcon || '⧉';
      button.setAttribute('title', button.dataset.defaultTitle || 'Copy');
      button.setAttribute('aria-label', button.dataset.defaultAriaLabel || button.dataset.defaultTitle || 'Copy');
    }, 1400);
  }

  function fallbackCopyText(text) {
    const helper = document.createElement('textarea');
    helper.value = text;
    helper.setAttribute('readonly', '');
    helper.style.position = 'fixed';
    helper.style.opacity = '0';
    helper.style.pointerEvents = 'none';
    document.body.appendChild(helper);
    helper.select();
    helper.setSelectionRange(0, helper.value.length);
    const ok = document.execCommand('copy');
    document.body.removeChild(helper);
    if (!ok) throw new Error('Clipboard copy failed.');
  }

  async function copyText(text) {
    if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(text);
    else fallbackCopyText(text);
  }

  async function copyFieldValue(fieldId, label, button) {
    const field = document.getElementById(fieldId);
    const value = String(field?.value || '');
    if (!value.trim()) {
      setUploadStatus(`${label} đang trống.`, 'warn');
      return;
    }
    try {
      await copyText(value);
      flashCopyButton(button);
    } catch (error) {
      setUploadStatus(`Không copy được ${label}.`, 'bad');
    }
  }

  function hideUploadPanel() {
    const panel = $('#uploadPanel');
    if (panel) panel.hidden = true;
    state.uploadProject = null;
    state.facebookCommentTargetId = '';
    setUploadStatus('');
    setUploadResult('');
    updateFacebookCommentButton();
  }

  async function loadUploadMetadata(projectName) {
    const title = $('#uploadTitle');
    const youtubeDescription = $('#youtubeDescription');
    const facebookCaption = $('#facebookCaption');
    const facebookSourceComment = $('#facebookSourceComment');
    const privacy = $('#youtubePrivacy');
    const facebookVideoState = $('#facebookVideoState');
    if (!title || !youtubeDescription || !facebookCaption) return;
    try {
      const response = await fetch(`/api/social/upload-metadata?project=${encodeURIComponent(projectName)}`, { cache: 'no-store' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      title.value = data.title || '';
      youtubeDescription.value = data.youtubeDescription || data.description || '';
      facebookCaption.value = data.facebookCaption || '';
      if (facebookSourceComment) facebookSourceComment.value = data.facebookSourceComment || '';
      if (privacy && data.privacyStatus) privacy.value = data.privacyStatus;
      if (facebookVideoState && data.facebookVideoState) facebookVideoState.value = data.facebookVideoState === 'PUBLISHED' ? 'PUBLISHED' : 'DRAFT';
    } catch (error) {
      setUploadStatus(error.message || String(error), 'bad');
    } finally {
      updateUploadBothButton();
      updateFacebookCommentButton();
    }
  }

  function updateFacebookCommentButton() {
    const button = $('#commentFacebookSource');
    if (!button) return;
    const hasComment = Boolean(($('#facebookSourceComment')?.value || '').trim());
    button.disabled = !(state.socialReady.facebook && state.facebookCommentTargetId && hasComment);
  }

  function updateUploadBothButton() {
    const uploadBothPublic = $('#uploadBothPublic');
    if (!uploadBothPublic) return;
    const isPublic = $('#youtubePrivacy')?.value === 'public' && $('#facebookVideoState')?.value === 'PUBLISHED';
    uploadBothPublic.disabled = !(isPublic && state.socialReady.youtube && state.socialReady.facebook);
    setButtonLabel(uploadBothPublic, isPublic ? 'Upload Facebook + YouTube + comment nguồn' : 'Chọn Public + Publish trước');
  }

  function setAccountAvatar(avatar, thumbnail) {
    if (!avatar) return;
    avatar.hidden = !thumbnail;
    avatar.onerror = () => {
      avatar.hidden = true;
      avatar.removeAttribute('src');
    };
    if (thumbnail) avatar.src = thumbnail;
    else avatar.removeAttribute('src');
  }

  function appendAccountContent(button, account, withChevron = false) {
    const accountId = String(account.id || '');
    const avatar = document.createElement('img');
    avatar.alt = '';
    setAccountAvatar(avatar, String(account.thumbnail || ''));

    const body = document.createElement('div');
    const name = document.createElement('strong');
    const id = document.createElement('span');
    name.textContent = String(account.title || account.name || accountId);
    id.textContent = `ID: ${accountId}`;
    body.append(name, id);
    button.append(avatar, body);
    if (withChevron) {
      const chevron = document.createElement('span');
      chevron.className = 'account-chevron';
      chevron.textContent = '⌄';
      button.appendChild(chevron);
    }
  }

  function closePlatformAccountMenus(exceptPrefix = '') {
    $all('.platform-account-list.open').forEach((list) => {
      if (exceptPrefix && list.id === `${exceptPrefix}AccountList`) return;
      list.classList.remove('open');
      const trigger = list.querySelector('.platform-account-trigger');
      if (trigger) trigger.setAttribute('aria-expanded', 'false');
    });
  }

  function renderPlatformAccounts(prefix, accounts = [], activeId = '') {
    const list = $(`#${prefix}AccountList`);
    if (!list) return;
    const normalized = accounts.filter((account) => account?.id);
    list.textContent = '';
    list.classList.remove('open');
    list.hidden = !normalized.length;
    if (!normalized.length) return;

    const activeAccount = normalized.find((account) => account.id === activeId || account.active) || normalized[0];
    const activeAccountId = String(activeAccount.id || '');
    const trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'platform-account platform-account-trigger active';
    trigger.dataset.accountId = activeAccountId;
    trigger.setAttribute('aria-haspopup', 'listbox');
    trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('title', normalized.length > 1 ? 'Bấm để chọn account khác' : 'Account đang chọn');
    appendAccountContent(trigger, activeAccount, normalized.length > 1);
    trigger.addEventListener('click', () => {
      if (normalized.length <= 1) return;
      const isOpen = list.classList.contains('open');
      closePlatformAccountMenus(prefix);
      list.classList.toggle('open', !isOpen);
      trigger.setAttribute('aria-expanded', !isOpen ? 'true' : 'false');
    });
    list.appendChild(trigger);

    if (normalized.length <= 1) return;

    const menu = document.createElement('div');
    menu.className = 'platform-account-options';
    menu.setAttribute('role', 'listbox');
    normalized.forEach((account) => {
      const accountId = String(account.id || '');
      const active = accountId === activeAccountId;
      const option = document.createElement('button');
      option.type = 'button';
      option.className = `platform-account platform-account-option ${active ? 'active' : ''}`;
      option.dataset.accountId = accountId;
      option.setAttribute('role', 'option');
      option.setAttribute('aria-selected', active ? 'true' : 'false');
      option.setAttribute('title', active ? 'Đang chọn' : 'Bấm để chọn account này');
      appendAccountContent(option, account);
      option.addEventListener('click', () => {
        closePlatformAccountMenus();
        if (!accountId || active) return;
        if (prefix === 'youtube') setYoutubeActiveChannel(accountId);
        else setFacebookActivePage(accountId);
      });
      menu.appendChild(option);
    });
    list.appendChild(menu);
  }

  function setAccountListDisabled(prefix, disabled) {
    $all(`#${prefix}AccountList button`).forEach((button) => {
      button.disabled = disabled;
    });
  }

  function accountListFallback(account = {}) {
    const accountId = String(account?.id || '');
    return accountId ? [account] : [];
  }

  function syncYoutubeChannels(youtube = {}) {
    const fallbackChannel = accountListFallback(youtube.channel);
    const channels = Array.isArray(youtube.channels) && youtube.channels.length ? youtube.channels : fallbackChannel;
    const activeChannelId = String(youtube.active_channel_id || youtube.channel?.id || channels.find((channel) => channel.active)?.id || '');
    renderPlatformAccounts('youtube', channels, activeChannelId);
  }

  function syncFacebookPages(facebook = {}) {
    const pages = Array.isArray(facebook.pages) ? facebook.pages : [];
    const activePageId = String(facebook.active_page_id || facebook.page_id || facebook.page?.id || pages.find((page) => page.active)?.id || '');
    renderPlatformAccounts('facebook', pages.length ? pages : accountListFallback(facebook.page), activePageId);
  }

  function syncFacebookConfigUi(facebook = {}) {
    const pageIdInput = $('#facebookPageId');
    const tokenInput = $('#facebookPageAccessToken');
    const configState = $('#facebookConfigState');
    const activePageId = String(facebook.active_page_id || facebook.page_id || facebook.page?.id || '').trim();
    const modalOpen = Boolean($('#facebookConfigModal') && !$('#facebookConfigModal').hidden);
    state.facebookActivePageId = activePageId;
    if (pageIdInput && document.activeElement !== pageIdInput && activePageId) {
      pageIdInput.value = activePageId;
    }
    if (tokenInput) {
      if (!modalOpen && document.activeElement !== tokenInput) tokenInput.value = '';
      tokenInput.placeholder = facebook.configured
        ? 'Đã lưu token, dán token mới nếu muốn đổi'
        : 'Dán Page access token';
    }
    if (configState) {
      configState.textContent = '';
      configState.hidden = true;
    }
  }

  function openFacebookConfigModal() {
    const modal = $('#facebookConfigModal');
    const pageIdInput = $('#facebookPageId');
    const tokenInput = $('#facebookPageAccessToken');
    if (!modal) return;
    modal.hidden = false;
    if (pageIdInput && !pageIdInput.value.trim() && state.facebookActivePageId) {
      pageIdInput.value = state.facebookActivePageId;
    }
    if (tokenInput) {
      tokenInput.value = '';
      tokenInput.focus();
    } else if (pageIdInput) {
      pageIdInput.focus();
    }
  }

  function closeFacebookConfigModal() {
    const modal = $('#facebookConfigModal');
    const tokenInput = $('#facebookPageAccessToken');
    if (tokenInput) tokenInput.value = '';
    if (modal) modal.hidden = true;
  }

  async function setYoutubeActiveChannel(channelId) {
    if (!channelId) return;
    setAccountListDisabled('youtube', true);
    setUploadStatus('Đang đổi YouTube Channel...', 'warn');
    try {
      const response = await fetch('/api/social/youtube/active-channel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channelId }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      setUploadStatus('Đã đổi YouTube Channel.', 'good');
      await refreshSocialStatus();
    } catch (error) {
      setUploadStatus(error.message || String(error), 'bad');
    } finally {
      setAccountListDisabled('youtube', false);
    }
  }

  async function setFacebookActivePage(pageId) {
    if (!pageId) return;
    setAccountListDisabled('facebook', true);
    setUploadStatus('Đang đổi Facebook Page...', 'warn');
    try {
      const response = await fetch('/api/social/facebook/active-page', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pageId }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      setUploadStatus('Đã đổi Facebook Page.', 'good');
      await refreshSocialStatus();
    } catch (error) {
      setUploadStatus(error.message || String(error), 'bad');
    } finally {
      setAccountListDisabled('facebook', false);
    }
  }

  async function refreshSocialStatus() {
    const connectYoutube = $('#connectYoutube');
    const uploadYoutube = $('#uploadYoutube');
    const uploadFacebook = $('#uploadFacebook');
    const commentFacebookSource = $('#commentFacebookSource');
    const facebookVideoState = $('#facebookVideoState');
    if (!connectYoutube || !uploadYoutube) return;
    try {
      const response = await fetch('/api/social/status', { cache: 'no-store' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      const youtube = data.platforms?.youtube || {};
      const facebook = data.platforms?.facebook || {};
      const canYoutube = Boolean(youtube.configured && youtube.connected);
      const canFacebook = Boolean(facebook.available);
      state.socialReady = { youtube: canYoutube, facebook: canFacebook };
      syncYoutubeChannels(youtube);
      syncFacebookPages(facebook);
      syncFacebookConfigUi(facebook);
      setButtonLabel(connectYoutube, 'Thêm channel');
      uploadYoutube.disabled = !canYoutube;
      if (uploadFacebook) {
        uploadFacebook.disabled = !canFacebook;
        setButtonLabel(uploadFacebook, canFacebook ? 'Upload Facebook Reels' : 'Cấu hình Facebook');
      }
      updateFacebookCommentButton();
      if (facebookVideoState && facebook.video_state) facebookVideoState.value = facebook.video_state === 'PUBLISHED' ? 'PUBLISHED' : 'DRAFT';
      const ready = [];
      if (canYoutube) ready.push('YouTube');
      if (canFacebook) ready.push('Facebook Reels');
      if (ready.length) {
        setUploadStatus(`${ready.join(', ')} đã sẵn sàng.`, 'good');
      } else {
        const missingYoutube = !youtube.configured;
        const missingFacebook = !facebook.configured;
        if (missingYoutube && missingFacebook) {
          setUploadStatus('Chưa cấu hình Social API. Bấm Hướng dẫn YouTube hoặc Hướng dẫn Facebook để xem cách cấu hình.', 'warn');
        } else {
          const nextSteps = [];
          if (youtube.configured && !youtube.connected) nextSteps.push('YouTube đã có config. Bấm Thêm channel để kết nối kênh.');
          if (missingYoutube) nextSteps.push(youtube.message || 'YouTube chưa cấu hình. Bấm Hướng dẫn YouTube để xem cách cấu hình.');
          if (missingFacebook) nextSteps.push(facebook.message || 'Facebook chưa cấu hình. Bấm Hướng dẫn Facebook để xem cách cấu hình.');
          setUploadStatus(nextSteps[0] || 'Chưa cấu hình Social API. Bấm hướng dẫn để xem cách cấu hình.', 'warn');
        }
      }
      updateUploadBothButton();
    } catch (error) {
      state.socialReady = { youtube: false, facebook: false };
      syncFacebookConfigUi({ configured: false });
      uploadYoutube.disabled = true;
      if (uploadFacebook) uploadFacebook.disabled = true;
      if (commentFacebookSource) commentFacebookSource.disabled = true;
      updateUploadBothButton();
      updateFacebookCommentButton();
      setUploadStatus(error.message || String(error), 'bad');
    }
  }

  async function showUploadPanel(projectName, videoUrl) {
    const panel = $('#uploadPanel');
    if (!panel) return;
    state.uploadProject = projectName;
    state.outputUrl = videoUrl || state.outputUrl;
    state.facebookCommentTargetId = '';
    panel.hidden = false;
    setUploadEmpty(projectName, false);
    setUploadResult('');
    await loadUploadMetadata(projectName);
    await refreshSocialStatus();
  }

  function setRenderState(title = '', steps = [], tone = 'running') {
    const panel = $('#renderState');
    const titleEl = $('#stateTitle');
    const list = $('#stateList');
    if (!panel || !titleEl || !list) return;
    panel.hidden = !title;
    panel.className = `render-state ${tone}`;
    titleEl.textContent = title;
    list.textContent = '';
    const lines = Array.isArray(steps) ? steps : [steps];
    lines.filter(Boolean).slice(-1).forEach((step) => {
      const item = document.createElement('li');
      item.textContent = step;
      list.appendChild(item);
    });
  }

  function formatElapsed(seconds) {
    const totalSeconds = Math.max(0, Math.floor(seconds || 0));
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const remainingSeconds = totalSeconds % 60;
    if (hours) return `${hours}h${minutes}m${remainingSeconds}s`;
    if (minutes) return `${minutes}m${remainingSeconds}s`;
    return `${remainingSeconds}s`;
  }

  function elapsedForJob(job) {
    const startedAt = Number(job.started_at || job.created_at || 0);
    if (!startedAt) return '0s';
    const finishedAt = Number(job.finished_at || 0);
    const endedAt = ['done', 'failed', 'cancelled'].includes(job.status) && finishedAt ? finishedAt : Date.now() / 1000;
    return formatElapsed(endedAt - startedAt);
  }

  function renderTitle(label, job) {
    return `${label} (đã chạy ${elapsedForJob(job)})`;
  }

  function latestRawLogLine(logs = '') {
    const lines = String(logs).split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    return lines.length ? lines[lines.length - 1] : '';
  }

  function renderProgressForJob(job) {
    const logs = job.logs || '';
    const rawLine = latestRawLogLine(logs);
    let progress = {
      title: 'Bắt đầu render...',
      log: rawLine,
    };

    [
      [/Speeding up audio|Saved sped-up audio/, 'Đang xử lý audio...'],
      [/Generating Edge TTS|Generating per-slide TTS|Slide \d+ TTS/, 'Đang tạo audio...'],
      [/Whisper transcription|Transcribing audio|Aligning transcript|Splitting audio/, 'Đang tách voiceover...'],
      [/Concatenating|voiceover_concat|Timing saved/, 'Đang ghép timing...'],
      [/Mapping check|Click timeline/, 'Đang kiểm tra slide...'],
      [/Recording slides|Recording\s+\d|Raw video/, 'Đang record slide...'],
      [/Merging voiceover|Final video|Video rendered successfully|All done|Done:/, 'Sắp hoàn thành...'],
    ].forEach(([pattern, title]) => {
      if (pattern.test(logs)) progress = { title, log: rawLine };
    });

    if (job.status === 'done') return { title: 'Hoàn tất render', log: rawLine };
    if (job.status === 'failed') return { title: 'Render thất bại', log: job.error || rawLine };
    if (job.status === 'cancelled') return { title: 'Đã dừng render', log: rawLine || 'Render đã được dừng.' };
    if (job.status === 'cancelling') return { title: 'Đang dừng render...', log: rawLine || 'Đang gửi tín hiệu dừng job render.' };
    return progress;
  }

  function setEngine(engine) {
    state.engine = engine;
    $all('[data-engine]').forEach((button) => {
      button.classList.toggle('active', button.dataset.engine === engine);
    });
    $all('[data-pane]').forEach((pane) => {
      pane.hidden = pane.dataset.pane !== engine;
    });
    syncAdvancedSettings();
  }

  function syncAdvancedSettings() {
    $all('[data-advanced-engine]').forEach((pane) => {
      pane.hidden = pane.dataset.advancedEngine !== state.engine;
    });
    const details = $('#advancedSettings');
    const label = $('#advancedStateLabel');
    if (details && label) label.textContent = details.open ? 'Đang mở' : 'Đang ẩn';
  }

  function syncSpeedPresets() {
    const speedInput = $('#renderSpeed');
    const value = speedInput ? Number(speedInput.value || 0) : 0;
    $all('.speed-preset[data-speed]').forEach((button) => {
      button.classList.toggle('active', Number(button.dataset.speed) === value);
    });
  }

  function currentElevenMode() {
    return document.querySelector('input[name="elevenMode"]:checked')?.value || 'upload';
  }

  function syncElevenMode() {
    const mode = currentElevenMode();
    $all('[data-eleven-mode-pane]').forEach((pane) => {
      pane.hidden = pane.dataset.elevenModePane !== mode;
    });
  }

  function syncElevenLabsApiKeyUi(configured) {
    const panel = $('#elevenApiKeyPanel');
    const apiState = $('#elevenApiKeyState');
    if (panel) panel.hidden = Boolean(configured);
    if (apiState) {
      apiState.textContent = configured
        ? 'Đã lưu API key trong config/tts.json'
        : 'Chưa lưu API key';
    }
  }

  async function loadElevenLabsConfig() {
    const input = $('#elevenVoice');
    if (!input) return;
    try {
      const response = await fetch('/api/tts/elevenlabs/config', { cache: 'no-store' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      input.value = data.voice_id || '';
      input.placeholder = data.voice_id || 'JBFqnCBsd6RMkjVDRZzb';
      syncElevenLabsApiKeyUi(Boolean(data.api_key_configured));
    } catch (error) {
      setStatus(error.message || String(error), 'bad');
    }
  }

  async function saveElevenLabsVoice() {
    const input = $('#elevenVoice');
    const voiceId = input?.value.trim() || '';
    if (!voiceId) {
      return;
    }
    if (elevenVoiceSaving) return;
    elevenVoiceSaving = true;
    try {
      const response = await fetch('/api/tts/elevenlabs/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voice_id: voiceId }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      if (input) input.value = data.voice_id || voiceId;
      setStatus('Đã lưu ElevenLabs voice ID vào config/tts.json.', 'good');
    } catch (error) {
      setStatus(error.message || String(error), 'bad');
    } finally {
      elevenVoiceSaving = false;
    }
  }

  function scheduleElevenLabsVoiceSave(delay = 450) {
    const input = $('#elevenVoice');
    if (!input || !input.value.trim()) return;
    if (elevenVoiceSaveTimer) window.clearTimeout(elevenVoiceSaveTimer);
    elevenVoiceSaveTimer = window.setTimeout(() => {
      elevenVoiceSaveTimer = null;
      saveElevenLabsVoice();
    }, delay);
  }

  async function saveElevenLabsApiKey() {
    const input = $('#elevenApiKey');
    const apiKey = input?.value.trim() || '';
    if (!apiKey) {
      return;
    }
    if (elevenApiKeySaving) return;
    elevenApiKeySaving = true;
    const apiState = $('#elevenApiKeyState');
    if (apiState) apiState.textContent = 'Đang lưu API key...';
    try {
      const response = await fetch('/api/tts/elevenlabs/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      if (input) input.value = '';
      syncElevenLabsApiKeyUi(Boolean(data.api_key_configured));
      setStatus('Đã lưu ElevenLabs API key vào config/tts.json.', 'good');
    } catch (error) {
      setStatus(error.message || String(error), 'bad');
      if (apiState) apiState.textContent = 'Lưu API key thất bại';
    } finally {
      elevenApiKeySaving = false;
    }
  }

  function scheduleElevenLabsApiKeySave(delay = 450) {
    const input = $('#elevenApiKey');
    if (!input || !input.value.trim()) return;
    if (elevenApiKeySaveTimer) window.clearTimeout(elevenApiKeySaveTimer);
    elevenApiKeySaveTimer = window.setTimeout(() => {
      elevenApiKeySaveTimer = null;
      saveElevenLabsApiKey();
    }, delay);
  }

  async function copyProjectScript(projectName, button) {
    const project = String(projectName || '').trim();
    if (!project) {
      setStatus('Không tìm thấy project để copy script.', 'bad');
      return;
    }
    if (button) button.disabled = true;
    try {
      const response = await fetch(`/api/slide-script?project=${encodeURIComponent(project)}`, { cache: 'no-store' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      const text = Array.isArray(data.lines) ? data.lines.join('\n') : '';
      if (!text.trim()) throw new Error(`${project} chưa có script-90s.txt hoặc script đang trống.`);
      await copyText(text);
      flashCopyButton(button);
      setStatus(`Đã copy script của ${project}.`, 'good');
    } catch (error) {
      setStatus(error.message || String(error), 'bad');
    } finally {
      if (button) button.disabled = false;
    }
  }

  function updateProjectUrl(projectName) {
    if (window.location.pathname !== '/') return;
    const url = new URL(window.location.href);
    url.searchParams.set('project', projectName);
    window.history.replaceState(null, '', url);
  }

  function setSelectedProject(projectName, updateUrl = true) {
    const project = projectMap.get(projectName);
    if (!project) {
      setStatus('Chưa có dự án slide nào để render.', 'bad');
      return;
    }

    state.project = project.name;
    state.outputUrl = project.output_url || project.video_url || `/slide/${encodeURIComponent(project.name)}/output/final_video.mp4`;

    const select = $('#projectSelect');
    if (select) select.value = project.name;
    setProjectVideoBadge(project);

    const selectedName = $('#selectedName');
    if (selectedName) selectedName.textContent = project.name;

    const selectedBadge = $('#selectedBadge');
    if (selectedBadge) selectedBadge.textContent = `${project.script_count || '?'} slide`;

    const previewLink = $('#previewLink');
    if (previewLink) previewLink.href = project.url;

    const existingVideoLink = $('#existingVideoLink');
    if (existingVideoLink) {
      existingVideoLink.href = project.video_url || state.outputUrl;
      existingVideoLink.hidden = !project.video_url;
    }

    const videoLink = $('#videoLink');
    if (videoLink) {
      videoLink.href = project.video_url || state.outputUrl;
      videoLink.hidden = true;
    }
    setRevealOutputButton(project.name, !state.busy && Boolean(project.video_url));
    setUploadCenterLink(project.name, Boolean(project.video_url));

    $all('.project-row[data-project]').forEach((row) => row.classList.toggle('selected', row.dataset.project === project.name));
    $all('.select-btn').forEach((button) => button.classList.toggle('active', button.dataset.project === project.name));

    if (!state.busy) {
      setRenderState('', []);
      if (project.video_url) {
        setStatus('', 'warn');
        showUploadPanel(project.name, project.video_url);
      } else {
        hideUploadPanel();
        setUploadEmpty(project.name, Boolean($('#uploadPanel')));
        setStatus(window.location.pathname === '/upload' ? `${project.name} chưa có final_video.mp4. Render ở Dashboard trước khi upload.` : '', project.has_script ? 'warn' : 'bad');
      }
    }
    if (updateUrl) updateProjectUrl(project.name);
  }

  function markProjectHasOutput(projectName, videoUrl) {
    const project = projectMap.get(projectName);
    if (project) {
      project.video_url = videoUrl;
      project.has_output = true;
    }

    const row = rowForProject(projectName);
    const deleteButton = row ? row.querySelector('.delete-output-btn[data-project]') : null;
    if (deleteButton) {
      deleteButton.disabled = false;
      deleteButton.classList.remove('disabled');
    }
    const slot = row ? row.querySelector('.row-video-slot') : null;
    if (slot) {
      slot.textContent = '';
      slot.classList.remove('muted');
      const link = document.createElement('a');
      link.className = 'small-link icon-btn';
      link.href = videoUrl;
      link.target = '_blank';
      link.rel = 'noreferrer';
      link.innerHTML = '<span class="btn-icon">▶</span><span>Mở</span>';
      slot.appendChild(link);
    }

    const existingVideoLink = $('#existingVideoLink');
    if (existingVideoLink && state.project === projectName) {
      existingVideoLink.href = videoUrl;
      existingVideoLink.hidden = false;
    }
    if (state.project === projectName) setRevealOutputButton(projectName, true);
    if (state.project === projectName) setUploadCenterLink(projectName, true);
    if (state.project === projectName) setProjectVideoBadge(project);
  }

  function markProjectOutputDeleted(projectName) {
    const project = projectMap.get(projectName);
    if (project) {
      project.video_url = null;
      project.has_output = false;
    }

    const row = rowForProject(projectName);
    const deleteButton = row ? row.querySelector('.delete-output-btn[data-project]') : null;
    if (deleteButton) {
      deleteButton.disabled = true;
      deleteButton.classList.add('disabled');
    }
    const slot = row ? row.querySelector('.row-video-slot') : null;
    if (slot) {
      slot.textContent = '';
      slot.classList.remove('muted');
      const disabled = document.createElement('span');
      disabled.className = 'icon-btn disabled';
      disabled.innerHTML = '<span class="btn-icon">▶</span><span>Mở</span>';
      slot.appendChild(disabled);
    }

    if (state.project === projectName) {
      const existingVideoLink = $('#existingVideoLink');
      if (existingVideoLink) existingVideoLink.hidden = true;
      const videoLink = $('#videoLink');
      if (videoLink) videoLink.hidden = true;
      setRevealOutputButton(projectName, false);
      setUploadCenterLink(projectName, false);
      setProjectVideoBadge(project);
      setUploadEmpty(projectName, Boolean($('#uploadPanel')));
      hideUploadPanel();
    }
  }

  async function revealOutput(projectName) {
    const project = projectMap.get(projectName || state.project);
    if (!project) {
      setStatus('Không tìm thấy dự án để mở output.', 'bad');
      return;
    }
    const button = $('#revealOutput');
    if (button) button.disabled = true;
    setStatus(`Đang mở vị trí final_video.mp4 của ${project.name}...`, 'warn');
    try {
      const response = await fetch('/api/output/reveal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project: project.name }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      setStatus(`Đã mở vị trí final_video.mp4 của ${project.name}.`, 'good');
    } catch (error) {
      setStatus(error.message || String(error), 'bad');
    } finally {
      if (button) button.disabled = false;
    }
  }

  async function deleteOutput(projectName) {
    const project = projectMap.get(projectName);
    if (!project) {
      setStatus('Không tìm thấy dự án để xoá output.', 'bad');
      return;
    }
    if (!project.has_output) {
      setStatus(`${project.name} chưa có output để xoá.`, 'warn');
      return;
    }

    const confirmed = window.confirm(
      `Xoá toàn bộ thư mục output của "${project.name}"?\n\nHành động này sẽ xoá final_video.mp4 và các file render cache trong thư mục output của project.`
    );
    if (!confirmed) return;

    const buttons = [
      ...$all('.delete-output-btn[data-project]').filter((button) => button.dataset.project === project.name),
      $('#deleteSelectedOutput'),
    ].filter(Boolean);
    buttons.forEach((button) => { button.disabled = true; });
    setStatus(`Đang xoá output của ${project.name}...`, 'warn');

    try {
      const response = await fetch('/api/output/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project: project.name, confirm: true }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);

      markProjectOutputDeleted(project.name);
      setStatus(data.deleted ? `Đã xoá output của ${project.name}.` : `${project.name} chưa có output để xoá.`, 'good');
    } catch (error) {
      setStatus(error.message || String(error), 'bad');
      setRenderState('Không thể xoá output', [error.message || String(error)], 'failed');
    } finally {
      buttons.forEach((button) => {
        const isProjectButton = button.classList.contains('delete-output-btn');
        button.disabled = isProjectButton && !project.has_output;
        if (isProjectButton) button.classList.toggle('disabled', !project.has_output);
      });
    }
  }

  function fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = String(reader.result || '');
        resolve(result.includes(',') ? result.split(',', 2)[1] : result);
      };
      reader.onerror = () => reject(reader.error || new Error('Không đọc được file audio.'));
      reader.readAsDataURL(file);
    });
  }

  function assertFileSize(file, maxBytes, label) {
    if (!file) return;
    if (file.size > maxBytes) {
      const maxMb = Math.round(maxBytes / 1024 / 1024);
      throw new Error(`${label} lớn hơn ${maxMb} MB.`);
    }
  }

  function openBrandConfigModal() {
    const modal = $('#brandConfigModal');
    if (!modal) return;
    const nameInput = $('#brandNameInput');
    const logoInput = $('#brandLogoFile');
    const logoName = $('#brandLogoFileName');
    if (nameInput) nameInput.value = state.renderOptions.brandName || '@nicetechchannels';
    if (logoInput) logoInput.value = '';
    if (logoName) {
      logoName.textContent = state.renderOptions.brandLogoFile
        ? state.renderOptions.brandLogoFile.name
        : 'Chưa chọn logo';
    }
    modal.hidden = false;
  }

  function closeBrandConfigModal() {
    const modal = $('#brandConfigModal');
    if (modal) modal.hidden = true;
  }

  function saveBrandConfig() {
    const name = ($('#brandNameInput')?.value || '').trim();
    if (name.length > 64) {
      setStatus('Tên brand tối đa 64 ký tự.', 'bad');
      return;
    }
    const logoFile = $('#brandLogoFile')?.files?.[0] || null;
    try {
      assertFileSize(logoFile, MAX_BRAND_LOGO_BYTES, 'File logo');
    } catch (error) {
      setStatus(error.message || String(error), 'bad');
      return;
    }
    state.renderOptions.brandName = name || '@nicetechchannels';
    if (logoFile) state.renderOptions.brandLogoFile = logoFile;
    closeBrandConfigModal();
    setStatus('Đã áp dụng tuỳ chỉnh Logo + brand cho lần render tới.', 'good');
  }

  async function startRender() {
    const startButton = $('#startRender');
    const stopButton = $('#stopRender');
    const videoLink = $('#videoLink');
    if (startButton) startButton.disabled = true;
    if (stopButton) {
      stopButton.hidden = true;
      stopButton.disabled = true;
    }
    if (videoLink) videoLink.hidden = true;
    setRevealOutputButton(state.project, false);
    state.busy = true;
    state.canceling = false;
    setRenderState('Đang chuẩn bị render', ['Kiểm tra project và thông số render.']);

    try {
      const project = currentProject();
      if (!project) throw new Error('Vui lòng chọn một dự án slide trước.');

      const payload = {
        project: project.name,
        engine: state.engine,
        speed: Number($('#renderSpeed').value || 1.1),
        size: $('#renderSize')?.value || '720x1280',
        outro: $('#renderOutro')?.checked !== false,
        branding: $('#renderBranding')?.checked !== false,
      };
      if (payload.outro && state.renderOptions.outroFile) {
        assertFileSize(state.renderOptions.outroFile, MAX_RENDER_VIDEO_BYTES, 'File outro');
        setRenderState('Đang chuẩn bị render', [`Đang nạp outro: ${state.renderOptions.outroFile.name}`]);
        payload.outroFile = {
          name: state.renderOptions.outroFile.name,
          data: await fileToBase64(state.renderOptions.outroFile),
        };
      }
      if (payload.branding) {
        payload.brandName = state.renderOptions.brandName || '@nicetechchannels';
        if (state.renderOptions.brandLogoFile) {
          assertFileSize(state.renderOptions.brandLogoFile, MAX_BRAND_LOGO_BYTES, 'File logo');
          setRenderState('Đang chuẩn bị render', [`Đang nạp logo: ${state.renderOptions.brandLogoFile.name}`]);
          payload.brandLogo = {
            name: state.renderOptions.brandLogoFile.name,
            data: await fileToBase64(state.renderOptions.brandLogoFile),
          };
        }
      }

      if (state.engine === 'elevenlabs') {
        payload.mode = currentElevenMode();
        if (payload.mode === 'upload') {
          const file = $('#elevenFile')?.files?.[0];
          if (!file) throw new Error('Vui lòng chọn file audio ElevenLabs trước.');
          if (file.size > MAX_AUDIO_BYTES) throw new Error('File audio lớn hơn 200 MB.');
          setRenderState('Đang chuẩn bị render', [`Đang nạp file audio: ${file.name}`]);
          payload.audio = {
            name: file.name,
            data: await fileToBase64(file),
          };
        } else {
          payload.voice = $('#elevenVoice')?.value.trim() || '';
          payload.force = Boolean($('#elevenForce')?.checked);
          setRenderState('Đang chuẩn bị render', ['ElevenLabs API: eleven_v3 gọi full script 1 lần, model khác mới tách từng slide nếu hỗ trợ context.']);
        }
      } else {
        payload.voice = $('#edgeVoice').value.trim() || 'vi-VN-HoaiMyNeural';
        payload.force = $('#edgeForce').checked;
        payload.edgePerSlide = Boolean($('#edgePerSlide')?.checked);
        setRenderState(
          'Đang chuẩn bị render',
          [payload.edgePerSlide ? 'Edge TTS sẽ tạo từng slide như luồng cũ.' : 'Edge TTS sẽ gọi full script 1 lần rồi split voiceover.']
        );
      }

      const response = await fetch('/api/render', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);

      state.jobId = data.id;
      if (stopButton) {
        stopButton.hidden = false;
        stopButton.disabled = false;
      }
      const progress = renderProgressForJob(data);
      setStatus(`Đã bắt đầu job render: ${data.id}`, 'good');
      setRenderState(renderTitle(progress.title, data), [progress.log]);
      await pollJob();
      if (state.pollTimer) window.clearInterval(state.pollTimer);
      state.pollTimer = window.setInterval(pollJob, 1500);
    } catch (error) {
      state.busy = false;
      setStatus(error.message || String(error), 'bad');
      setRenderState('Không thể bắt đầu render', [error.message || String(error)], 'failed');
      if (startButton) startButton.disabled = false;
      if (stopButton) {
        stopButton.hidden = true;
        stopButton.disabled = true;
      }
    }
  }

  async function stopRender() {
    if (!state.jobId || state.canceling) return;
    const confirmed = window.confirm('Dừng job render đang chạy? Audio/video đang tạo dở có thể còn lại trong thư mục output.');
    if (!confirmed) return;
    const stopButton = $('#stopRender');
    if (stopButton) stopButton.disabled = true;
    state.canceling = true;
    setStatus('Đang dừng render...', 'warn');
    setRenderState('Đang dừng render...', ['Đang gửi tín hiệu dừng job render.']);
    try {
      const response = await fetch(`/api/jobs/${state.jobId}/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      const job = await response.json();
      if (!response.ok) throw new Error(job.error || `HTTP ${response.status}`);
      const progress = renderProgressForJob(job);
      setRenderState(renderTitle(progress.title, job), [progress.log], job.status === 'cancelled' ? 'cancelled' : 'running');
    } catch (error) {
      state.canceling = false;
      if (stopButton) stopButton.disabled = false;
      setStatus(error.message || String(error), 'bad');
      setRenderState('Không thể dừng render', [error.message || String(error)], 'failed');
    }
  }

  async function pollJob() {
    if (!state.jobId) return;
    const startButton = $('#startRender');
    const stopButton = $('#stopRender');
    const videoLink = $('#videoLink');

    try {
      const response = await fetch(`/api/jobs/${state.jobId}`, { cache: 'no-store' });
      const job = await response.json();
      if (!response.ok) throw new Error(job.error || `HTTP ${response.status}`);

      const progress = renderProgressForJob(job);
      if (job.status === 'done') {
        if (state.pollTimer) window.clearInterval(state.pollTimer);
        state.pollTimer = null;
        state.busy = false;
        state.canceling = false;
        if (startButton) startButton.disabled = false;
        if (stopButton) {
          stopButton.hidden = true;
          stopButton.disabled = true;
        }
        const finalUrl = job.video_url || state.outputUrl;
        setStatus('Render hoàn tất. final_video.mp4 đã sẵn sàng.', 'good');
        setRenderState(renderTitle(progress.title, job), [progress.log], 'done');
        if (videoLink) {
          videoLink.href = finalUrl;
          videoLink.hidden = false;
        }
        setRevealOutputButton(job.project || state.project, true);
        markProjectHasOutput(job.project || state.project, finalUrl);
        await showUploadPanel(job.project || state.project, finalUrl);
      } else if (job.status === 'failed') {
        if (state.pollTimer) window.clearInterval(state.pollTimer);
        state.pollTimer = null;
        state.busy = false;
        state.canceling = false;
        if (startButton) startButton.disabled = false;
        if (stopButton) {
          stopButton.hidden = true;
          stopButton.disabled = true;
        }
        setStatus(progress.log || 'Render thất bại.', 'bad');
        setRenderState(renderTitle(progress.title, job), [progress.log], 'failed');
      } else if (job.status === 'cancelled') {
        if (state.pollTimer) window.clearInterval(state.pollTimer);
        state.pollTimer = null;
        state.busy = false;
        state.canceling = false;
        if (startButton) startButton.disabled = false;
        if (stopButton) {
          stopButton.hidden = true;
          stopButton.disabled = true;
        }
        setStatus('Đã dừng render.', 'warn');
        setRenderState(renderTitle(progress.title, job), [progress.log], 'cancelled');
      } else {
        if (stopButton) {
          stopButton.hidden = false;
          stopButton.disabled = job.status === 'cancelling' || state.canceling;
        }
        setStatus(job.status === 'queued' ? 'Render đang chờ xử lý...' : 'Render đang chạy...', 'warn');
        setRenderState(renderTitle(progress.title, job), [progress.log]);
      }
    } catch (error) {
      if (state.pollTimer) window.clearInterval(state.pollTimer);
      state.pollTimer = null;
      state.busy = false;
      state.canceling = false;
      if (startButton) startButton.disabled = false;
      if (stopButton) {
        stopButton.hidden = true;
        stopButton.disabled = true;
      }
      setStatus(error.message || String(error), 'bad');
      setRenderState('Lỗi khi đọc trạng thái render', [error.message || String(error)], 'failed');
    }
  }

  $all('[data-engine]').forEach((button) => {
    button.addEventListener('click', () => setEngine(button.dataset.engine));
  });

  $all('input[name="elevenMode"]').forEach((input) => {
    input.addEventListener('change', syncElevenMode);
  });
  syncElevenMode();

  const advancedSettings = $('#advancedSettings');
  if (advancedSettings) {
    advancedSettings.open = localStorage.getItem('nicetechchannels-render-advanced-open-v3') === '1';
    advancedSettings.addEventListener('toggle', () => {
      localStorage.setItem('nicetechchannels-render-advanced-open-v3', advancedSettings.open ? '1' : '0');
      syncAdvancedSettings();
    });
  }
  syncAdvancedSettings();
  loadElevenLabsConfig();

  const elevenVoiceInput = $('#elevenVoice');
  if (elevenVoiceInput) {
    elevenVoiceInput.addEventListener('paste', () => {
      window.setTimeout(() => scheduleElevenLabsVoiceSave(80), 0);
    });
    elevenVoiceInput.addEventListener('input', () => scheduleElevenLabsVoiceSave(700));
  }

  const elevenApiKeyInput = $('#elevenApiKey');
  if (elevenApiKeyInput) {
    elevenApiKeyInput.addEventListener('paste', () => {
      window.setTimeout(() => scheduleElevenLabsApiKeySave(80), 0);
    });
    elevenApiKeyInput.addEventListener('input', () => scheduleElevenLabsApiKeySave(700));
  }

  $all('.speed-preset[data-speed]').forEach((button) => {
    button.addEventListener('click', () => {
      const speedInput = $('#renderSpeed');
      if (speedInput) speedInput.value = button.dataset.speed;
      syncSpeedPresets();
    });
  });

  const speedInput = $('#renderSpeed');
  if (speedInput) speedInput.addEventListener('input', syncSpeedPresets);

  const elevenFileInput = $('#elevenFile');
  const elevenFileName = $('#elevenFileName');
  if (elevenFileInput && elevenFileName) {
    elevenFileInput.addEventListener('change', () => {
      const file = elevenFileInput.files?.[0];
      elevenFileName.textContent = file ? file.name : 'Chưa chọn file';
    });
  }

  const chooseOutroButton = $('#chooseOutro');
  const outroFileInput = $('#outroFile');
  if (chooseOutroButton && outroFileInput) {
    chooseOutroButton.addEventListener('click', () => outroFileInput.click());
    outroFileInput.addEventListener('change', () => {
      const file = outroFileInput.files?.[0] || null;
      try {
        assertFileSize(file, MAX_RENDER_VIDEO_BYTES, 'File outro');
        state.renderOptions.outroFile = file;
        if (file) setStatus(`Đã chọn outro: ${file.name}`, 'good');
      } catch (error) {
        outroFileInput.value = '';
        state.renderOptions.outroFile = null;
        setStatus(error.message || String(error), 'bad');
      }
    });
  }

  const brandLogoInput = $('#brandLogoFile');
  const brandLogoFileName = $('#brandLogoFileName');
  if (brandLogoInput && brandLogoFileName) {
    brandLogoInput.addEventListener('change', () => {
      const file = brandLogoInput.files?.[0] || null;
      brandLogoFileName.textContent = file ? file.name : (state.renderOptions.brandLogoFile?.name || 'Chưa chọn logo');
    });
  }

  const openBrandConfigButton = $('#openBrandConfig');
  if (openBrandConfigButton) openBrandConfigButton.addEventListener('click', openBrandConfigModal);

  const saveBrandConfigButton = $('#saveBrandConfig');
  if (saveBrandConfigButton) saveBrandConfigButton.addEventListener('click', saveBrandConfig);

  ['#closeBrandConfig', '#cancelBrandConfig'].forEach((selector) => {
    const button = $(selector);
    if (button) button.addEventListener('click', closeBrandConfigModal);
  });

  const brandConfigModal = $('#brandConfigModal');
  if (brandConfigModal) {
    brandConfigModal.addEventListener('click', (event) => {
      if (event.target === brandConfigModal) closeBrandConfigModal();
    });
  }

  const projectSelect = $('#projectSelect');
  if (projectSelect) {
    projectSelect.addEventListener('change', () => setSelectedProject(projectSelect.value));
  }

  $all('.select-btn').forEach((button) => {
    button.addEventListener('click', () => setSelectedProject(button.dataset.project));
  });

  $all('.delete-output-btn[data-project]').forEach((button) => {
    button.addEventListener('click', () => deleteOutput(button.dataset.project));
  });

  $all('.copy-script-btn[data-project]').forEach((button) => {
    button.addEventListener('click', () => copyProjectScript(button.dataset.project, button));
  });

  const deleteSelectedOutput = $('#deleteSelectedOutput');
  if (deleteSelectedOutput) {
    deleteSelectedOutput.addEventListener('click', () => deleteOutput(state.project));
  }

  const revealOutputButton = $('#revealOutput');
  if (revealOutputButton) {
    revealOutputButton.addEventListener('click', () => revealOutput(revealOutputButton.dataset.project || state.project));
  }

  const stopRenderButton = $('#stopRender');
  if (stopRenderButton) {
    stopRenderButton.addEventListener('click', stopRender);
  }

  async function uploadYoutubeVideo(project) {
    const response = await fetch('/api/social/youtube/upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project,
        title: $('#uploadTitle')?.value || '',
        description: $('#youtubeDescription')?.value || '',
        privacyStatus: $('#youtubePrivacy')?.value || 'public',
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    return data;
  }

  async function uploadFacebookReel(project, facebookVideoState = $('#facebookVideoState')?.value || 'PUBLISHED') {
    const response = await fetch('/api/social/facebook/upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project,
        facebookCaption: $('#facebookCaption')?.value || '',
        facebookVideoState,
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    return data;
  }

  async function commentFacebookSource(project) {
    const response = await fetch('/api/social/facebook/comment-source', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project,
        sourceCommentTargetId: state.facebookCommentTargetId,
        facebookSourceComment: $('#facebookSourceComment')?.value || '',
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    return data;
  }

  async function saveFacebookConfig() {
    const pageIdInput = $('#facebookPageId');
    const tokenInput = $('#facebookPageAccessToken');
    const button = $('#saveFacebookConfig');
    const pageId = pageIdInput?.value.trim() || '';
    const pageAccessToken = tokenInput?.value.trim() || '';
    if (!pageId || !pageAccessToken) {
      setUploadStatus('Nhập đủ Facebook Page ID và Page access token trước khi lưu.', 'bad');
      return;
    }
    if (facebookConfigSaving) return;
    facebookConfigSaving = true;
    if (button) button.disabled = true;
    setUploadStatus('Đang lưu cấu hình Facebook...', 'warn');
    try {
      const response = await fetch('/api/social/facebook/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pageId, pageAccessToken }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
      if (tokenInput) tokenInput.value = '';
      if (pageIdInput) pageIdInput.value = data.active_page_id || pageId;
      await refreshSocialStatus();
      setUploadStatus('Đã lưu Facebook Page ID và Page access token vào config/social-upload.json.', 'good');
      closeFacebookConfigModal();
    } catch (error) {
      setUploadStatus(error.message || String(error), 'bad');
    } finally {
      facebookConfigSaving = false;
      if (button) button.disabled = false;
    }
  }

  const connectYoutube = $('#connectYoutube');
  if (connectYoutube) {
    connectYoutube.addEventListener('click', () => {
      const project = state.uploadProject || state.project;
      if (!project) {
        setUploadStatus('Vui lòng render hoặc chọn project trước.', 'bad');
        return;
      }
      window.open(`/api/social/youtube/connect?project=${encodeURIComponent(project)}`, '_blank', 'noopener,noreferrer');
      setUploadStatus('Đã mở tab Google OAuth. Kết nối xong quay lại tab này để upload.', 'warn');
    });
  }

  const uploadYoutube = $('#uploadYoutube');
  if (uploadYoutube) {
    uploadYoutube.addEventListener('click', async () => {
      const project = state.uploadProject || state.project;
      if (!project) {
        setUploadStatus('Vui lòng render project trước.', 'bad');
        return;
      }
      uploadYoutube.disabled = true;
      setUploadResult('');
      setUploadStatus('Đang upload lên YouTube...', 'warn');
      try {
        const data = await uploadYoutubeVideo(project);
        setUploadStatus('Upload YouTube xong. Mở Studio để kiểm tra và publish nếu cần.', 'good');
        setUploadResult(data.message || 'Uploaded.', 'good', [
          { label: 'Mở video', href: data.url },
          { label: 'Mở Studio', href: data.studio_url },
        ]);
      } catch (error) {
        setUploadStatus(error.message || String(error), 'bad');
      } finally {
        await refreshSocialStatus();
      }
    });
  }

  const uploadFacebook = $('#uploadFacebook');
  if (uploadFacebook) {
    uploadFacebook.addEventListener('click', async () => {
      const project = state.uploadProject || state.project;
      if (!project) {
        setUploadStatus('Vui lòng render project trước.', 'bad');
        return;
      }
      const facebookVideoState = $('#facebookVideoState')?.value || 'PUBLISHED';
      uploadFacebook.disabled = true;
      setUploadResult('');
      setUploadStatus(`Đang upload Facebook Reels (${facebookVideoState})...`, 'warn');
      try {
        const data = await uploadFacebookReel(project, facebookVideoState);
        state.facebookCommentTargetId = facebookVideoState === 'PUBLISHED' ? (data.source_comment_target_id || data.post_id || data.video_id || '') : '';
        updateFacebookCommentButton();
        setUploadStatus(data.message || 'Upload Facebook Reels xong.', 'good');
        const links = [];
        if (data.url) links.push({ label: 'Mở Reel/Post', href: data.url });
        setUploadResult(data.message || 'Uploaded.', 'good', links);
      } catch (error) {
        setUploadStatus(error.message || String(error), 'bad');
      } finally {
        await refreshSocialStatus();
      }
    });
  }

  const commentFacebookSourceButton = $('#commentFacebookSource');
  if (commentFacebookSourceButton) {
    commentFacebookSourceButton.addEventListener('click', async () => {
      const project = state.uploadProject || state.project;
      if (!project) {
        setUploadStatus('Vui lòng render project trước.', 'bad');
        return;
      }
      if (!state.facebookCommentTargetId) {
        setUploadStatus('Upload Facebook Reels ở trạng thái Publish now trước, rồi bấm Comment source.', 'bad');
        return;
      }
      if (!(($('#facebookSourceComment')?.value || '').trim())) {
        setUploadStatus('Source comment đang trống.', 'bad');
        return;
      }
      commentFacebookSourceButton.disabled = true;
      setUploadStatus('Đang comment source lên Facebook...', 'warn');
      try {
        const data = await commentFacebookSource(project);
        setUploadStatus(data.message || 'Comment source xong.', 'good');
        setUploadResult(data.message || 'Source comment posted.', 'good');
      } catch (error) {
        setUploadStatus(error.message || String(error), 'bad');
      } finally {
        updateFacebookCommentButton();
      }
    });
  }

  const saveFacebookConfigButton = $('#saveFacebookConfig');
  if (saveFacebookConfigButton) {
    saveFacebookConfigButton.addEventListener('click', saveFacebookConfig);
  }

  const openFacebookConfigButton = $('#openFacebookConfig');
  if (openFacebookConfigButton) {
    openFacebookConfigButton.addEventListener('click', openFacebookConfigModal);
  }

  ['#closeFacebookConfig', '#cancelFacebookConfig'].forEach((selector) => {
    const button = $(selector);
    if (button) button.addEventListener('click', closeFacebookConfigModal);
  });

  const facebookConfigModal = $('#facebookConfigModal');
  if (facebookConfigModal) {
    facebookConfigModal.addEventListener('click', (event) => {
      if (event.target === facebookConfigModal) closeFacebookConfigModal();
    });
  }

  const uploadBothPublic = $('#uploadBothPublic');
  if (uploadBothPublic) {
    uploadBothPublic.addEventListener('click', async () => {
      const project = state.uploadProject || state.project;
      if (!project) {
        setUploadStatus('Vui lòng render project trước.', 'bad');
        return;
      }
      if ($('#youtubePrivacy')?.value !== 'public' || $('#facebookVideoState')?.value !== 'PUBLISHED') {
        setUploadStatus('Chọn YouTube Public và Reels Publish now trước.', 'bad');
        updateUploadBothButton();
        return;
      }
      const links = [];
      uploadBothPublic.disabled = true;
      if (uploadYoutube) uploadYoutube.disabled = true;
      if (uploadFacebook) uploadFacebook.disabled = true;
      setUploadResult('');
      setUploadStatus('Đang upload Facebook Reels trước...', 'warn');
      try {
        const facebookData = await uploadFacebookReel(project, 'PUBLISHED');
        const facebookUploadedAt = Date.now();
        state.facebookCommentTargetId = facebookData.source_comment_target_id || facebookData.post_id || facebookData.video_id || '';
        updateFacebookCommentButton();
        if (facebookData.url) links.push({ label: 'Mở Reel/Post', href: facebookData.url });
        setUploadStatus('Facebook Reels xong. Đang upload YouTube...', 'warn');
        const youtubeData = await uploadYoutubeVideo(project);
        if (youtubeData.url) links.push({ label: 'Mở YouTube', href: youtubeData.url });
        if (youtubeData.studio_url) links.push({ label: 'Mở Studio', href: youtubeData.studio_url });
        const sourceComment = ($('#facebookSourceComment')?.value || '').trim();
        if (sourceComment) {
          if (!state.facebookCommentTargetId) {
            throw new Error('Facebook upload xong nhưng chưa có Reel/Post ID để comment nguồn.');
          }
          const commentData = await commentFacebookSourceWithDelay(project, facebookUploadedAt);
          setUploadResult(commentData.message || 'Đã comment nguồn lên Facebook.', 'good', links);
        } else {
          setUploadResult('Đã upload public cả hai nền tảng. Source comment đang trống nên bỏ qua bước comment.', 'good', links);
        }
        setUploadStatus('Upload Facebook, YouTube và xử lý nguồn xong.', 'good');
      } catch (error) {
        setUploadStatus(error.message || String(error), 'bad');
        if (links.length) setUploadResult('Một phần đã upload xong trước khi lỗi.', 'warn', links);
      } finally {
        await refreshSocialStatus();
      }
    });
  }

  ['#youtubePrivacy', '#facebookVideoState'].forEach((selector) => {
    const control = $(selector);
    if (control) control.addEventListener('change', updateUploadBothButton);
  });
  const facebookSourceComment = $('#facebookSourceComment');
  if (facebookSourceComment) facebookSourceComment.addEventListener('input', updateFacebookCommentButton);
  $all('[data-copy-target]').forEach((button) => {
    button.addEventListener('click', () => copyFieldValue(
      button.dataset.copyTarget || '',
      button.dataset.copyLabel || 'Nội dung này',
      button,
    ));
  });

  document.addEventListener('click', (event) => {
    if (!event.target.closest('.platform-account-list')) closePlatformAccountMenus();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closePlatformAccountMenus();
      closeFacebookConfigModal();
      closeBrandConfigModal();
    }
  });

  window.addEventListener('focus', () => {
    const panel = $('#uploadPanel');
    if (panel && !panel.hidden) refreshSocialStatus();
  });

  const refreshProjects = $('#refreshProjects');
  if (refreshProjects) {
    refreshProjects.addEventListener('click', () => window.location.reload());
  }

  $all('[data-source-root-select]').forEach((button) => {
    button.addEventListener('click', selectSourceRootFromFinder);
  });

  const storedTheme = localStorage.getItem('nicetechchannels-theme');
  applyTheme(storedTheme || 'light');
  $all('[data-theme-toggle]').forEach((button) => {
    button.addEventListener('click', toggleTheme);
  });

  $all('.project-row[data-project]').forEach((row) => {
    row.addEventListener('click', (event) => {
      if (event.target.closest('a, button')) return;
      setSelectedProject(row.dataset.project);
    });
  });

  const startButton = $('#startRender');
  if (startButton) startButton.addEventListener('click', startRender);

  const initialFromUrl = new URLSearchParams(window.location.search).get('project');
  const initialProject = window.__INITIAL_PROJECT__ || initialFromUrl || projects[0]?.name;
  if (initialProject) setSelectedProject(initialProject, false);
  syncSpeedPresets();
})();
