// KitchenIQ Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // 1. Initialize ApexCharts
    initTrendChart();
    initBrandDonutChart();
    initWasteDonutChart();
    
    // Close dropdowns when clicking outside
    window.addEventListener('click', function(e) {
        const profileWidget = document.querySelector('.profile-info');
        const profileDropdown = document.getElementById('profileDropdown');
        if (profileDropdown && profileDropdown.classList.contains('show')) {
            if (!profileWidget.contains(e.target)) {
                profileDropdown.classList.remove('show');
            }
        }
    });
});

// Toggle User Profile Dropdown
function toggleProfileDropdown() {
    const dropdown = document.getElementById('profileDropdown');
    dropdown.classList.toggle('show');
}

// Switch Item Tab: Top Items vs Bottom Items
function switchItemTab(tab) {
    const topTable = document.getElementById('topItemsTable');
    const bottomTable = document.getElementById('bottomItemsTable');
    const tabButtons = document.querySelectorAll('.table-tabs .tab-btn');
    
    if (tab === 'top') {
        topTable.classList.remove('hidden');
        bottomTable.classList.add('hidden');
        tabButtons[0].classList.add('active');
        tabButtons[1].classList.remove('active');
    } else {
        topTable.classList.add('hidden');
        bottomTable.classList.remove('hidden');
        tabButtons[0].classList.remove('active');
        tabButtons[1].classList.add('active');
    }
}

// Trigger Django page reload on Brand/Site selection
function filterData() {
    const siteSelect = document.getElementById('siteFilter');
    const brandSelect = document.getElementById('brandFilter');
    
    const siteVal = siteSelect.value;
    const brandVal = brandSelect.value;
    
    window.location.href = `?site=${siteVal}&brand=${brandVal}`;
}

// 1. Sales & Margin Trend Chart (Area / Line Chart)
function initTrendChart() {
    const chartContainer = document.querySelector('#salesMarginChart');
    if (!chartContainer) return;
    
    const options = {
        series: [
            {
                name: 'Sales (' + currencySymbol + ')',
                data: chartSalesData // Loaded from templates
            },
            {
                name: 'Contribution Margin (' + currencySymbol + ')',
                data: chartMarginData // Loaded from templates
            }
        ],
        chart: {
            type: 'area',
            height: 270,
            toolbar: {
                show: false
            },
            zoom: {
                enabled: false
            },
            fontFamily: 'Inter, sans-serif'
        },
        colors: ['#10B981', '#8B5CF6'], // Green for sales, Purple for margin
        dataLabels: {
            enabled: false
        },
        stroke: {
            curve: 'smooth',
            width: 2
        },
        fill: {
            type: 'gradient',
            gradient: {
                shadeIntensity: 1,
                opacityFrom: 0.25,
                opacityTo: 0.05,
                stops: [0, 90, 100]
            }
        },
        xaxis: {
            categories: chartDates,
            labels: {
                style: {
                    colors: '#64748b',
                    fontSize: '11px'
                }
            },
            axisBorder: {
                show: false
            },
            axisTicks: {
                show: false
            }
        },
        yaxis: {
            labels: {
                formatter: function (value) {
                    if (value >= 1000) {
                        return currencySymbol + (value / 1000) + 'K';
                    }
                    return currencySymbol + value;
                },
                style: {
                    colors: '#64748b',
                    fontSize: '11px'
                }
            }
        },
        grid: {
            borderColor: '#e2e8f0',
            strokeDashArray: 4,
            xaxis: {
                lines: {
                    show: false
                }
            },
            yaxis: {
                lines: {
                    show: true
                }
            }
        },
        legend: {
            position: 'top',
            horizontalAlign: 'left',
            fontFamily: 'Inter',
            fontSize: '12px',
            markers: {
                radius: 12
            }
        },
        tooltip: {
            y: {
                formatter: function (val) {
                    return currencySymbol + val.toLocaleString();
                }
            }
        }
    };

    const chart = new ApexCharts(chartContainer, options);
    chart.render();
}

// 2. Donut Chart - Margin by Brand
function initBrandDonutChart() {
    const chartContainer = document.querySelector('#marginBrandChart');
    if (!chartContainer) return;
    
    // Total calculation
    const totalValue = brandValues.reduce((a, b) => a + b, 0);
    
    const options = {
        series: brandValues,
        labels: brandLabels,
        colors: brandColors,
        chart: {
            type: 'donut',
            height: 250,
            fontFamily: 'Inter, sans-serif'
        },
        stroke: {
            show: true,
            width: 2,
            colors: ['#ffffff']
        },
        dataLabels: {
            enabled: false
        },
        legend: {
            position: 'bottom',
            fontFamily: 'Inter',
            fontSize: '11px',
            markers: {
                radius: 12
            }
        },
        plotOptions: {
            pie: {
                donut: {
                    size: '70%',
                    labels: {
                        show: true,
                        name: {
                            show: true,
                            fontSize: '12px',
                            color: '#64748b',
                            offsetY: -8
                        },
                        value: {
                            show: true,
                            fontSize: '20px',
                            fontFamily: 'Outfit, sans-serif',
                            fontWeight: '700',
                            color: '#0f172a',
                            offsetY: 8,
                            formatter: function (val) {
                                return currencySymbol + parseInt(val).toLocaleString();
                            }
                        },
                        total: {
                            show: true,
                            label: 'Total',
                            color: '#64748b',
                            fontSize: '12px',
                            formatter: function (w) {
                                return currencySymbol + totalValue.toLocaleString();
                            }
                        }
                    }
                }
            }
        },
        tooltip: {
            y: {
                formatter: function (val) {
                    return currencySymbol + val.toLocaleString();
                }
            }
        }
    };

    const chart = new ApexCharts(chartContainer, options);
    chart.render();
}

// 3. Donut Chart - Waste Risk Overview
function initWasteDonutChart() {
    const chartContainer = document.querySelector('#wasteRiskChart');
    if (!chartContainer) return;
    
    const options = {
        series: [wasteRiskData.high, wasteRiskData.medium, wasteRiskData.low],
        labels: ['High Risk', 'Medium Risk', 'Low Risk'],
        colors: ['#ef4444', '#f97316', '#22c55e'], // Red, Orange, Green
        chart: {
            type: 'donut',
            height: 230,
            fontFamily: 'Inter, sans-serif'
        },
        stroke: {
            show: true,
            width: 2,
            colors: ['#ffffff']
        },
        dataLabels: {
            enabled: false
        },
        legend: {
            position: 'bottom',
            fontFamily: 'Inter',
            fontSize: '11px',
            markers: {
                radius: 12
            }
        },
        plotOptions: {
            pie: {
                donut: {
                    size: '72%',
                    labels: {
                        show: true,
                        name: {
                            show: false
                        },
                        value: {
                            show: true,
                            fontSize: '22px',
                            fontFamily: 'Outfit, sans-serif',
                            fontWeight: '800',
                            color: '#0f172a',
                            offsetY: 6,
                            formatter: function (val) {
                                return val;
                            }
                        },
                        total: {
                            show: true,
                            label: 'High Risk',
                            color: '#0f172a',
                            formatter: function (w) {
                                return wasteRiskData.total + '\nHigh Risk';
                            }
                        }
                    }
                }
            }
        },
        tooltip: {
            y: {
                formatter: function (val) {
                    return val + ' Ingredients';
                }
            }
        }
    };

    const chart = new ApexCharts(chartContainer, options);
    chart.render();
}
