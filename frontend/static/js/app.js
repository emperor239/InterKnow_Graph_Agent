(() => {
  const chartDom = document.getElementById('chart');
  if (!chartDom) {
    console.error('未找到图表容器 #chart');
    throw new Error('找不到图表容器');
  }
  if (!window.echarts) {
    document.getElementById('infoPanel').textContent = 'ECharts 未加载成功，请检查网络或重试。';
    throw new Error('ECharts not loaded');
  }
  const myChart = echarts.init(chartDom);
  let currentGraph = { nodes: [], links: [] };

  function setInfo(text) {
    const panel = document.getElementById('infoPanel');
    if (panel) panel.textContent = text;
  }

  function renderGraph(data) {
    currentGraph = data;
    const categoriesArr = Array.from(new Set((data.nodes || []).map(n => n.discipline || '其他')));
    const categories = categoriesArr.map(name => ({ name }));

    const nodes = (data.nodes || []).map(n => ({
      id: n.id,
      name: n.name || n.id,
      symbolSize: 8 + (n.value || 8),
      category: categoriesArr.indexOf(n.discipline || '其他'),
      value: n.value || 1
    }));
    const links = (data.links || []).map(l => ({
      source: l.source,
      target: l.target,
      label: { show: true, formatter: l.relation || '' }
    }));

    // const option = {
    //   tooltip: { formatter: params => params.data.name || params.data.id },
    //   legend: [{ data: categoriesArr }],
    //   series: [{
    //     type: 'graph',
    //     layout: 'force',
    //     roam: true,
    //     draggable: true,
    //     data: nodes,
    //     links: links,
    //     categories,
    //     emphasis: { focus: 'adjacency' },
    //     force: { repulsion: 280, edgeLength: [60, 140] },
    //     label: { position: 'right' }
    //   }]
    // };

    const option = {
      tooltip: { 
      // 重构formatter：显示name + 额外描述
      formatter: (params) => {
        // 基础名称/ID
        const baseInfo = params.data.name || params.data.id;
        // 额外描述（有则显示，无则提示“无描述”）
        const descInfo = params.data.description 
          ? `<br/><br/>📝 描述：${params.data.description}` 
          : "<br/><br/>📝 描述：暂无";
        // 拼接返回
        return baseInfo + descInfo;
      },
      textStyle: { 
        color: '#ffffff',
        fontSize: 16,
        fontWeight: 'bold'
      },
      backgroundColor: 'rgba(0,0,0,0.7)',
      borderColor: '#ffffff'
    },
      legend: [{ 
        data: categoriesArr,
        textStyle: { 
          color: '#ffffff',
          fontSize: 18,
          fontWeight: 'bold'
        }
      }],
      series: [{
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        data: nodes,
        links: links,
        categories,
        emphasis: { 
          focus: 'adjacency',
          label: { 
            color: '#ffffff',
            fontSize: 20,
            fontWeight: 'bold'
          },
          // 悬浮时节点进一步放大
          itemStyle: { symbolSize: 60 },
          // 悬浮时边进一步加粗
          lineStyle: { width: 6 }
        },
        // 力导向参数适配：放大后节点不重叠
        force: { 
          repulsion: 450,    // 节点排斥力增大（默认280→450）
          edgeLength: [100, 180] // 边长度加长（默认60-140→100-180）
        },
        // 节点核心样式：放大+白色文字+加粗
        label: { 
          position: 'right',
          color: '#ffffff',
          fontSize: 18,
          fontWeight: 'bold',
          fontFamily: 'Arial'
        },
        // 节点大小（核心放大配置）
        symbolSize: 50, // 节点默认大小（默认10→50，可按需调40/60）
        // 节点样式（可选：加边框，更醒目）
        itemStyle: { 
          borderColor: '#ffffff', // 节点边框白色
          borderWidth: 2,         // 边框宽度
          opacity: 0.8            // 透明度，避免太厚重
        },
        // 边的样式：加粗放大
        lineStyle: { 
          width: 4,        // 边宽度（默认1→4，可按需调3/5）
          color: '#ffffff',// 边颜色设为白色（和文字匹配）
          opacity: 0.7     // 边透明度，避免抢焦点
        },
        category: {
          label: { 
            color: '#ffffff',
            fontSize: 18,
            fontWeight: 'bold'
          }
        },
        edgeLabel: {
          color: '#ffffff',
          fontSize: 14,
          fontWeight: 'bold'
        }
      }]
    };
    myChart.setOption(option);

    myChart.off('click');
    myChart.on('click', params => {
      if (params.dataType === 'node') showNodeInfo(params.data);
    });
  }

  function showNodeInfo(node) {
    const panel = document.getElementById('infoPanel');
    if (!panel) return;
    panel.innerHTML = '';
    const title = document.createElement('div');
    title.className = 'node-label';
    title.textContent = node.name || node.id;
    panel.appendChild(title);
    const details = document.createElement('div');
    details.innerHTML = `<b>ID:</b> ${node.id || ''}<br/><b>学科:</b> ${node.category || ''}<br/><b>值:</b> ${node.value || ''}`;
    panel.appendChild(details);
  }

  async function loadSample() {
    try {
      setInfo('正在加载本地样例...');
      const res = await fetch('/frontend/static/json/sample_data.json');
      if (!res.ok) throw new Error('样例文件未找到');
      const data = await res.json();
      renderGraph(data);
      setInfo('已加载本地样例，点击节点查看详情');
    } catch (err) {
      console.error('加载样例失败', err);
      setInfo('加载样例失败，请确认 sample_data.json 可访问');
      alert('加载样例失败，请检查 sample_data.json 是否存在并可访问');
    }
  }

  async function queryConcept(concept) {
    if (!concept) return alert('请输入概念');
    const skipBackend = document.getElementById('skipBackend')?.checked;
    if (skipBackend) {
      setInfo('离线模式：直接使用本地样例');
      await loadSample();
      return;
    }

    setInfo(`查询「${concept}」中...`);
    try {
      const controller = new AbortController();
      const timeout = setTimeout(()=>controller.abort(), 60000);
      const res = await fetch(`/api/graph`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ concept }),
        signal: controller.signal
      });
      clearTimeout(timeout);
      if (!res.ok) throw new Error('非 2xx 响应');
      const data = await res.json();
      const safeNodes = Array.isArray(data?.nodes) ? data.nodes : [];
      const safeLinks = Array.isArray(data?.links) ? data.links : [];

      if (safeNodes.length > 0) {
        renderGraph({ nodes: safeNodes, links: safeLinks });
        setInfo('已加载后端数据，点击节点查看详情');
        return;
      }

      console.warn('后端返回为空或无节点，改用本地样例', data);
      await loadSample();
      return;
    } catch (e) {
      console.warn('后端请求失败，使用本地样例。', e);
      setInfo('后端不可用，切换到本地样例...');
      await loadSample();
    }
  }

  function handleFileUpload(file) {
    const reader = new FileReader();
    reader.onload = e => {
      try {
        const data = JSON.parse(e.target.result);
        if (data.nodes && data.links) renderGraph(data);
        else alert('JSON 必须包含 nodes 与 links 字段');
      } catch (err) { alert('解析 JSON 失败'); }
    };
    reader.readAsText(file);
  }

  function exportJSON() {
    const blob = new Blob([JSON.stringify(currentGraph, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'graph_export.json';
    a.click();
    URL.revokeObjectURL(url);
  }

  function bindEvents() {
    const queryBtn = document.getElementById('queryBtn');
    const loadSampleBtn = document.getElementById('loadSampleBtn');
    const fileInput = document.getElementById('fileInput');
    const exportBtn = document.getElementById('exportBtn');

    if (!queryBtn || !loadSampleBtn || !fileInput || !exportBtn) {
      console.error('按钮或输入控件未找到，无法绑定事件');
      setInfo('页面加载不完整，请刷新重试');
      return;
    }

    loadSampleBtn.addEventListener('click', loadSample);
    queryBtn.addEventListener('click', () => queryConcept(document.getElementById('conceptInput').value.trim()));
    fileInput.addEventListener('change', e => { if (e.target.files[0]) handleFileUpload(e.target.files[0]); });
    exportBtn.addEventListener('click', exportJSON);
  }

  window.addEventListener('DOMContentLoaded', () => {
    bindEvents();
    loadSample();
  });
})();
