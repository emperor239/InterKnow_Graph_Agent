var app = {};

var chartDom = document.getElementById('count_and_tokens');
var myChart = echarts.init(chartDom);
var option;

// 生成X轴时间数据
const categories = (function () {
    let now = new Date();
    let res = [];
    let len = 10;
    while (len--) {
        res.unshift(now.toLocaleTimeString().replace(/^\D*/, ''));
        now = new Date(+now - 2000);
    }
    return res;
})();
// 生成X轴数字数据
const categories2 = (function () {
    let res = [];
    let len = 10;
    while (len--) {
        res.push(10 - len - 1);
    }
    return res;
})();
// 生成柱状图随机数据
const data = (function () {
    let res = [];
    let len = 10;
    while (len--) {
        res.push(Math.round(Math.random() * 1000));
    }
    return res;
})();
// 生成折线图随机数据
const data2 = (function () {
    let res = [];
    let len = 0;
    while (len < 10) {
        res.push(+(Math.random() * 10 + 5).toFixed(1));
        len++;
    }
    return res;
})();

// ECharts配置项
// option = {
//     title: {
//         text: 'Dynamic Data（动态数据图表）'
//     },
//     tooltip: {
//         trigger: 'axis',
//         axisPointer: {
//             type: 'cross',
//             label: {
//                 backgroundColor: '#ffffff'
//             }
//         }
//     },
//     legend: {},
//     toolbox: {
//         show: true,
//         feature: {
//             dataView: { readOnly: false },
//             restore: {},
//             saveAsImage: {}
//         }
//     },
//     dataZoom: {
//         show: false,
//         start: 0,
//         end: 100
//     },
//     xAxis: [
//         {
//             type: 'category',
//             boundaryGap: true,
//             data: categories
//         },
//         {
//             type: 'category',
//             boundaryGap: true,
//             data: categories2
//         }
//     ],
//     yAxis: [
//         {
//             type: 'value',
//             scale: true,
//             name: 'Price（价格）',
//             max: 30,
//             min: 0,
//             boundaryGap: [0.2, 0.2]
//         },
//         {
//             type: 'value',
//             scale: true,
//             name: 'Order（订单量）',
//             max: 1200,
//             min: 0,
//             boundaryGap: [0.2, 0.2]
//         }
//     ],
//     series: [
//         {
//             name: 'Dynamic Bar（动态柱状图）',
//             type: 'bar',
//             xAxisIndex: 1,
//             yAxisIndex: 1,
//             data: data
//         },
//         {
//             name: 'Dynamic Line（动态折线图）',
//             type: 'line',
//             data: data2
//         }
//     ]
// };


option = {
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'cross',
            label: {
                backgroundColor: '#0e85a9',
                color: '#ffffff' // 提示框标签文字黑色（白色背景更清晰）
            }
        },
        textStyle: { color: '#000000' } // 提示框内容文字白色
    },
    legend: {
        textStyle: { color: '#ffffff' } // 图例文字白色
    },
    toolbox: {
        show: true,
        iconStyle: { color: '#ffffff' }, // 工具箱图标白色
        feature: {
            dataView: { readOnly: false, textStyle: { color: '#ffffff' } },
            restore: { textStyle: { color: '#ffffff' } },
            saveAsImage: { textStyle: { color: '#ffffff' } }
        }
    },
    dataZoom: {
        show: false,
        start: 0,
        end: 100
    },
    xAxis: [
        {
            type: 'category',
            boundaryGap: true,
            data: categories,
            // X轴基础样式（白色）
            axisLine: { lineStyle: { color: '#ffffff' } }, // X轴线颜色
            axisTick: { lineStyle: { color: '#ffffff' } }, // X轴刻度线颜色
            axisLabel: { color: '#ffffff' }, // X轴标签文字颜色
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } } // X轴分割线（浅白，避免刺眼）
        },
        {
            type: 'category',
            boundaryGap: true,
            data: categories2,
            // 第二个X轴同样设为白色
            axisLine: { lineStyle: { color: '#ffffff' } },
            axisTick: { lineStyle: { color: '#ffffff' } },
            axisLabel: { color: '#ffffff' },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } }
        }
    ],
    yAxis: [
        {
            type: 'value',
            scale: true,
            name: 'Price（价格）',
            max: 30,
            min: 0,
            boundaryGap: [0.2, 0.2],
            // Y轴基础样式（白色）
            axisLine: { lineStyle: { color: '#ffffff' } }, // Y轴线颜色
            axisTick: { lineStyle: { color: '#ffffff' } }, // Y轴刻度线颜色
            axisLabel: { color: '#ffffff' }, // Y轴标签文字颜色
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } }, // Y轴分割线（浅白）
            nameTextStyle: { color: '#ffffff' } // Y轴名称文字白色
        },
        {
            type: 'value',
            scale: true,
            name: 'Order（订单量）',
            max: 1200,
            min: 0,
            boundaryGap: [0.2, 0.2],
            // 第二个Y轴同样设为白色
            axisLine: { lineStyle: { color: '#ffffff' } },
            axisTick: { lineStyle: { color: '#ffffff' } },
            axisLabel: { color: '#ffffff' },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } },
            nameTextStyle: { color: '#ffffff' }
        }
    ],
    series: [
        {
            name: 'Dynamic Bar（动态柱状图）',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: data,
            itemStyle: { color: 'rgba(15, 176, 163, 0.8)' } // 柱状图柱子浅白（适配深色背景）
        },
        {
            name: 'Dynamic Line（动态折线图）',
            type: 'line',
            data: data2,
            lineStyle: { color: '#054f25' }, // 折线颜色白色
            itemStyle: { color: '#0db851' }, // 折点颜色白色
            areaStyle: { color: 'rgba(255,255,255,0.2)' } // 折线面积填充（浅白）
        }
    ],
};

// 定时更新数据（每2.1秒刷新一次）
app.count = 11;
setInterval(function () {
    let axisData = new Date().toLocaleTimeString().replace(/^\D*/, '');
    // 移除第一个数据，新增随机数据（保持10个数据点）
    data.shift();
    data.push(Math.round(Math.random() * 1000));
    data2.shift();
    data2.push(+(Math.random() * 10 + 5).toFixed(1));
    categories.shift();
    categories.push(axisData);
    categories2.shift();
    categories2.push(app.count++);
    // 更新图表数据
    myChart.setOption({
        xAxis: [
            { data: categories },
            { data: categories2 }
        ],
        series: [
            { data: data },
            { data: data2 }
        ]
    });
}, 2100);

// 渲染图表
option && myChart.setOption(option);

// 可选：窗口大小变化时，自适应图表
window.addEventListener('resize', function() {
    myChart.resize();
});