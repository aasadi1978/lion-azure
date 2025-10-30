function add_listeners() {

    window.onload = function () {
      document.getElementById('chart-assign-drivers').style.display = 'block';
    };

    window.addEventListener('keydown', function (e) {
      if (e.ctrlKey && (e.key === 'p' || e.key === 'P')) {
        e.preventDefault();
        show_popup((id = 'id-manage-optimization'));
      }
    });

    window.addEventListener('keydown', function (e) {
      if (e.ctrlKey && (e.key === 'm' || e.key === 'M')) {
        e.preventDefault();
        show_popup('id-insert-movement-frame');
      }
    });

    window.addEventListener('keydown', function (e) {
      if (e.ctrlKey && (e.key === 'e' || e.key === 'E')) {
        e.preventDefault();
        export_local_schedule();
      }
    });

    window.addEventListener('keydown', function (e) {
      if (e.ctrlKey && (e.key === 'z' || e.key === 'Z')) {
        e.preventDefault();
        undo();
      }
    });

    window.addEventListener('keydown', function (e) {
      if (e.ctrlKey && (e.key === 'd' || e.key === 'D')) {
        e.preventDefault();
        show_popup((id = 'id-insert-driver-frame'));
      }
    });

    window.addEventListener('keydown', function (e) {
      if (e.ctrlKey && (e.key === 'l' || e.key === 'L')) {
        e.preventDefault();
        show_popup((id = 'id-insert-location-frame'));
      }
    });

    window.addEventListener('keydown', function (e) {
      if (e.ctrlKey && (e.key === 'r' || e.key === 'R')) {
        e.preventDefault();
        show_popup((id = 'id-manage-runtimes'));
      }
    });

    window.addEventListener('keydown', function (e) {
      if (e.keyCode === 116) {
        e.preventDefault();
        refresh_all();
      }
    });

    let prebutton2 = document.getElementById('btn-Previous');
    prebutton2.onclick = function () {
      prebutton2.focus();
      let curpg = window.currPage;
      curpg--;
      window.currPage = curpg;
      update_page_num(curpg);
      get_chart_data(page_num=curpg);
    };

    let nxtbutton2 = document.getElementById('btn-Next');
    nxtbutton2.onclick = function () {
      nxtbutton2.focus();
      let curpg = window.currPage;
      curpg++;
      window.currPage = curpg;
      update_page_num(curpg);
      document.getElementById('btn-Previous').disabled = false;
      get_chart_data(page_num=curpg);
    };
  
    let curpg = window.currPage;
    if (!curpg){
      curpg = 1
    }
    window.currPage = curpg;
    get_chart_data(page_num=curpg);
}

document.addEventListener('DOMContentLoaded', add_listeners)