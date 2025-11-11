/* Guestbook management system*/

class GuestbookManager(){
  constructor(){
    this.entries = [];
    this.filters = {
      search = '',
      dateRange = { start: null, end: null},
      sortBy: 'newest'
    };
    this.realtime = new RealtimeManager();
    this.analytics = new AnalyticsEngine();
    this.offlineManager = new OfflineManager();

    this.init();
  }

  async init(){
    await this.loadEntries();
    this.setupEventListeners();
    this.setupRealtimeUpdates();
    this.startAnalyticsTracking();
    this.offlineManager.init();

    //Initialize 
    this.initVoiceRecognition();
    this.initImageUpload();
    this.initAutoSave();
  }

  //Advanced entry management 

  async loadEntries(){
    try {
      const response = await fetch('/api/guestbook?extend=true');
      const data = await response.json();

      if (data.status === 'success'){
        this.entries = data.entries;
        this.renderEntries();
        this.analytics.trackEvent('entries_loaded', { count: this.entries.length });
      }
    } catch(error){
      console.error('Error loading entries: ', error);
      this.offlineManager.showOfflineMessage();
    }
  }

  setupAdvancedSearch(){
    const searchInput = document.getElementById('advanced-search');
    if(searchInput){
      let searchTimeout;

      searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          this.filters.search = e.target.value;
          this.applyFilters();
        }, 300);
      })
    }
  }
}
