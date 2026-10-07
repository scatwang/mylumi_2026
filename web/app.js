/**
 * NorCal FLL BIOGLOW 2026 - Master Comparison Table Application Logic
 */

let currentWeekendFilter = 'all';
let currentSearchTerm = '';
let currentSortColumn = 'date';
let currentSortDirection = 'asc';
let expandedRowIds = new Set();

document.addEventListener('DOMContentLoaded', () => {
  if (typeof window.BIOGLOW_DATA === 'undefined') {
    console.error('BIOGLOW_DATA not loaded!');
    return;
  }
  initApp();
});

function initApp() {
  renderMatrixTable();
  renderInductionTables();

  // Keyboard shortcut: ESC closes modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal();
    }
  });
}

/**
 * Toggle City vs Weekend Induction Panel
 */
function toggleInductionPanel() {
  const panel = document.getElementById('induction-panel');
  const btn = document.getElementById('btn-toggle-induction');
  if (!panel) return;

  const isHidden = panel.style.display === 'none';
  panel.style.display = isHidden ? 'block' : 'none';
  if (btn) {
    btn.classList.toggle('active', isHidden);
  }
}

/**
 * Switch Induction Sub-tabs
 */
function switchInductionTab(tabKey) {
  document.querySelectorAll('.ind-tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  const activeBtn = document.getElementById(`tab-btn-${tabKey}`);
  if (activeBtn) activeBtn.classList.add('active');

  ['region', 'weekend', 'sensitivity'].forEach(key => {
    const el = document.getElementById(`tab-content-${key}`);
    if (el) {
      el.style.display = key === tabKey ? 'block' : 'none';
    }
  });
}

let currentInductionDataset = '2025';

/**
 * Switch Induction Dataset between 2025 and combined
 */
function switchInductionDataset(dsKey) {
  currentInductionDataset = dsKey;
  
  const btn2025 = document.getElementById('dataset-btn-2025');
  const btnComb = document.getElementById('dataset-btn-combined');
  if (btn2025) btn2025.classList.toggle('active', dsKey === '2025');
  if (btnComb) btnComb.classList.toggle('active', dsKey === 'combined');

  renderInductionTables();
}

/**
 * Render Induction Tables & Sensitive Breakdown
 */
function renderInductionTables() {
  const data = window.BIOGLOW_DATA;
  if (!data) return;

  const activeDs = (data.datasets && data.datasets[currentInductionDataset]) 
    ? data.datasets[currentInductionDataset] 
    : data;

  const isCombined = currentInductionDataset === 'combined';
  const ic = activeDs.impact_comparison || {};
  const regEff = ic.region_effect || {};
  const wkEff = ic.weekend_effect || {};

  // Update Dynamic Verdict Banner
  const titleEl = document.getElementById('verdict-banner-title');
  const textEl = document.getElementById('verdict-banner-text');
  if (titleEl && textEl) {
    if (isCombined) {
      titleEl.innerHTML = `🔥 2024+2025 双赛季聚合实证：样本翻倍至 36 场，彻底证实【Week 2 与 Week 3 中位数完全持平】的客观规律！`;
      textEl.innerHTML = `
        将 <strong>2024（SUBMERGED）</strong>与 <strong>2025（UNEARTHED）</strong>双赛季 <strong>36 场资格赛</strong>聚合分析后，核心归纳结果得到显著增强与验证：<br><br>
        ① <strong>Week 2 与 Week 3 中位数惊人一致（完全封顶停滞）</strong>：Week 2 场均中位数为 <strong>234.0 分</strong>，Week 3 为 <strong>233.4 分</strong>，两者落差仅 <strong>0.6 分</strong>！这在两个规则与任务完全不同的赛季中一致重现，无可辩驳地证实了：<strong>普通/腰部队伍在第 2 周已达到技术天花板，多 1 周时间并不能提升典型队伍的均值中位数</strong>。<br>
        ② <strong>大区影响力依然大幅碾压周次</strong>：大区解释了 <strong>15.5%</strong> 的中位数方差（SS = 9,646.0），是周次（5.6%，SS = 3,459.8）的 <strong>2.8 倍</strong>；大区落差达 <strong>71.9 分</strong>（东湾 205.6 vs 中央谷地 277.5），是周次跨度（31.5 分）的 <strong>2.3 倍</strong>。<br>
        ③ <strong>跨赛季各大区强弱排名 100% 保持稳定</strong>：中央谷地始终领跑（#1），半岛（#2）与南湾（#3）稳居核心高强区，旧金山（#4）与东湾（#5）居后，展现了NorCal各大区深层次工程教育与培训生态的长期连续性。<br>
        ④ <strong>清晰显露「Week 1 初赛冷启动效应」</strong>：2024 与 2025 赛季均表现出 Week 1 分数明显落后（场均中位数 202.5 分，比 W2/W3 低约 31 分），原因是初赛第一周各队机械与程序刚完成调试，极少有队伍能完整发挥。
      `;
    } else {
      titleEl.innerHTML = `核心结论：按大区（Region）分区后，【大区】对中位数分数的影响仍然远大于【周次】！`;
      textEl.innerHTML = `
        在单因素方差分析（ANOVA）中，<strong>大区（Region）解释了 18.1% 的中位数方差</strong>，而<strong>周次（Weekend）仅解释了 1.6%</strong>，大区的影响力是周次的 <strong>11.3 倍</strong>！
        大区之间平均中位数落差达 <strong>47.5 分</strong>（东湾 230.0 分 vs 萨克拉门托与中央谷地 277.5 分）；而跨周末的平均中位数极差仅为 <strong>14.7 分</strong>（Week 2 与 Week 3 几乎完全持平，仅差 1.3 分）。
        <strong>周次的核心影响在于拉高单场最高分上限（Max / Top 3），而大区直接决定了参赛群体的技术底盘和中位数基准。</strong>
      `;
    }
  }

  // Update Dynamic Stat Cards
  const regEtaEl = document.getElementById('stat-region-eta');
  const regSpanEl = document.getElementById('stat-region-span');
  const regSsEl = document.getElementById('stat-region-ss');
  const wkEtaEl = document.getElementById('stat-weekend-eta');
  const wkSpanEl = document.getElementById('stat-weekend-span');
  const wkDiffEl = document.getElementById('stat-weekend-diff');
  const ratioValEl = document.getElementById('stat-ratio-val');
  const ratioSpanEl = document.getElementById('stat-ratio-span');

  if (regEtaEl && regEff.variance_explained_pct !== undefined) {
    regEtaEl.textContent = `${regEff.variance_explained_pct.toFixed(1)}%`;
  }
  if (regSpanEl && regEff.range_pts !== undefined) {
    regSpanEl.textContent = `${regEff.range_pts.toFixed(1)} pts (${regEff.mean_min.toFixed(1)} ~ ${regEff.mean_max.toFixed(1)})`;
  }
  if (regSsEl && regEff.sum_of_squares !== undefined) {
    regSsEl.textContent = `SS = ${regEff.sum_of_squares.toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1})}`;
  }

  if (wkEtaEl && wkEff.variance_explained_pct !== undefined) {
    wkEtaEl.textContent = `${wkEff.variance_explained_pct.toFixed(1)}%`;
  }
  if (wkSpanEl && wkEff.range_pts !== undefined) {
    wkSpanEl.textContent = `${wkEff.range_pts.toFixed(1)} pts (${wkEff.mean_min.toFixed(1)} ~ ${wkEff.mean_max.toFixed(1)})`;
  }
  if (wkDiffEl) {
    wkDiffEl.innerHTML = isCombined 
      ? `<span class="text-emerald font-bold">仅 -0.6 pts (234.0 vs 233.4) 🎯</span>`
      : `<span class="text-cyan font-bold">仅 +1.3 pts (257.2 vs 258.5) 🎯</span>`;
  }

  if (ratioValEl && ic.variance_ratio !== undefined) {
    ratioValEl.textContent = `${ic.variance_ratio.toFixed(1)}x`;
  }
  if (ratioSpanEl && ic.range_ratio !== undefined) {
    ratioSpanEl.textContent = `${ic.range_ratio.toFixed(1)}x (${regEff.range_pts.toFixed(1)} / ${wkEff.range_pts.toFixed(1)})`;
  }

  // 1. Render Region Induction Table
  const tbodyRegion = document.getElementById('tbody-induction-region');
  const regInduction = activeDs.region_induction || data.region_induction || [];
  if (tbodyRegion && regInduction.length > 0) {
    tbodyRegion.innerHTML = regInduction.map((r, idx) => {
      const rankBadge = idx < 3 
        ? `<span class="rank-badge top-${idx+1}">${idx+1}</span>` 
        : `<span class="rank-badge">${idx+1}</span>`;
      
      const medianColor = r.mean_median >= 270 ? 'text-amber' : (r.mean_median >= 250 ? 'text-cyan' : (r.mean_median >= 225 ? 'text-emerald' : 'text-purple'));
      
      return `
        <tr>
          <td class="text-center">${rankBadge}</td>
          <td>
            <div class="fw-bold" style="font-size: 0.95rem;">${r.region}</div>
          </td>
          <td>
            <span class="region-pill text-xs">${r.cities_str}</span>
          </td>
          <td class="text-center font-mono">${r.events_count} 场</td>
          <td class="text-center font-mono text-dim">${r.total_teams || '-'} 队</td>
          <td class="text-center font-mono fw-bold ${medianColor}" style="font-size: 1.05rem;">
            ${r.mean_median.toFixed(1)}
          </td>
          <td class="text-center font-mono fw-bold text-cyan" style="font-size: 1.05rem;">
            ${r.pooled_median ? r.pooled_median.toFixed(1) : '-'}
          </td>
          <td class="text-center font-mono text-dim text-xs">
            ${r.min_median === r.max_median ? `${r.min_median.toFixed(1)}` : `${r.min_median.toFixed(1)} ~ ${r.max_median.toFixed(1)}`}
          </td>
          <td class="text-center font-mono text-cyan">${r.mean_top3 ? r.mean_top3.toFixed(1) : '-'}</td>
          <td class="text-center font-mono text-purple fw-bold">${r.mean_max ? r.mean_max.toFixed(1) : '-'}</td>
          <td class="text-center font-mono text-amber">${r.mean_cutoff ? r.mean_cutoff.toFixed(1) : '-'}</td>
          <td><span class="tier-pill ${r.tier_class}">${r.tier}</span></td>
        </tr>
      `;
    }).join('');
  }

  // 2. Render Weekend Induction Table
  const tbodyWk = document.getElementById('tbody-induction-weekend');
  const wkInduction = activeDs.weekend_induction || data.weekend_induction || [];
  const weekendDatesMap = {
    1: { dPast: '11/01 ~ 11/02', d2026: '11/07 ~ 11/08' },
    2: { dPast: '11/08 ~ 11/09', d2026: '11/14 ~ 11/15' },
    3: { dPast: '11/15 ~ 11/16', d2026: '11/21 ~ 11/22' }
  };

  if (tbodyWk && wkInduction.length > 0) {
    tbodyWk.innerHTML = wkInduction.map(w => {
      const wkClass = `wk-${w.weekend}`;
      const datesObj = weekendDatesMap[w.weekend] || { dPast: '-', d2026: '-' };
      const dPastText = isCombined ? `历届 11月第${w.weekend}周` : datesObj.dPast;

      return `
        <tr>
          <td>
            <span class="weekend-pill ${wkClass} fw-bold">${w.weekend_label}</span>
          </td>
          <td class="font-mono text-dim">${w.dates_2025 || dPastText}</td>
          <td class="font-mono text-cyan">${w.dates_2026 || datesObj.d2026}</td>
          <td class="text-center font-mono">${w.events_count} 场</td>
          <td class="text-center font-mono text-dim">${w.total_teams || '-'} 队</td>
          <td class="text-center font-mono fw-bold text-amber" style="font-size: 1.05rem;">
            ${w.mean_median.toFixed(1)}
          </td>
          <td class="text-center font-mono fw-bold text-cyan" style="font-size: 1.05rem;">
            ${w.pooled_median ? w.pooled_median.toFixed(1) : '-'}
          </td>
          <td class="text-center font-mono text-dim text-xs">
            ${w.min_median ? `${w.min_median.toFixed(1)} ~ ${w.max_median.toFixed(1)}` : '-'}
          </td>
          <td class="text-center font-mono text-cyan">${w.mean_top3 ? w.mean_top3.toFixed(1) : '-'}</td>
          <td class="text-center font-mono text-purple fw-bold">${w.mean_max ? w.mean_max.toFixed(1) : '-'}</td>
          <td class="text-center font-mono text-amber">${w.mean_cutoff ? w.mean_cutoff.toFixed(1) : '-'}</td>
          <td class="text-sm" style="max-width: 300px; line-height: 1.45;">
            ${w.insight}
          </td>
        </tr>
      `;
    }).join('');
  }

  // 3. Render Sensitivity Breakdown Table
  const tbodySens = document.getElementById('tbody-induction-sensitivity');
  const sensList = (ic && ic.metrics_sensitivity) ? ic.metrics_sensitivity : [];
  if (tbodySens && sensList.length > 0) {
    const explanations2025 = {
      "median_score": "大区完全主导（11.3x）。腰部队伍的实力由所在大区学校与俱乐部社群的成熟度与集训模式决定，多 1~2 周时间无法让中位数产生跨越式提升。",
      "mean_score": "大区占显著优势（5.0x）。赛事整体均分受大区参赛队伍整体底盘实力影响更深。",
      "advancement_cutoff": "大区主导（3.9x）。各赛区的晋级门槛主要受大区内部整体竞争激烈程度左右。",
      "top3_avg": "周次影响开始大幅上升（周次占 18.2%）。拔尖前三队伍利用周次延后进行高频迭代攻克多任务，但大区底蕴仍占 33.3%。",
      "max_score": "周次影响最强（周次占 19.4%）。冲刺全赛季单场 450+ 极限高分的队伍需要充分的 Week 3 冲刺调试时间。"
    };

    const explanationsCombined = {
      "median_score": "大区保持主导（2.8x）。跨两个赛季共 36 场数据验证：大区决定了基准底盘，Week 2 与 Week 3 中位数完全持平（234.0 vs 233.4）。",
      "mean_score": "大区保持主导（3.2x）。整体参赛队伍的平均分数主要取决于大区教育体系与师资梯队。",
      "advancement_cutoff": "周次略有上升（周次 4.7% vs 大区 1.8%）。因晋级线定义各赛区稍有差异，周次延后带来的拔尖队伍挤压效应开始显现。",
      "top3_avg": "大区与周次共同发力（大区占 16.1%，周次占 10.6%）。拔尖前三队伍既受大区顶级俱乐部氛围滋养，也借力后期调试时间拉大领先优势。",
      "max_score": "大区与周次协同（大区 9.1%，周次 6.4%）。单场最高分既需要大区强队出现，也依赖后期赛程的时间积淀。"
    };

    const expMap = isCombined ? explanationsCombined : explanations2025;

    tbodySens.innerHTML = sensList.map(s => {
      const isDominantRegion = s.dominant_factor.includes('大区');
      const regPct = s.region_explained_pct !== undefined ? s.region_explained_pct : s.city_explained_pct;
      return `
        <tr>
          <td class="fw-bold">${s.metric_label}</td>
          <td>
            <div class="d-flex align-center gap-2">
              <span class="font-mono text-cyan fw-bold">${regPct.toFixed(1)}%</span>
              <div class="progress-track" style="width: 100px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden;">
                <div style="width: ${Math.min(100, regPct * 2.5)}%; height: 100%; background: var(--cyan-neon);"></div>
              </div>
            </div>
          </td>
          <td>
            <div class="d-flex align-center gap-2">
              <span class="font-mono text-purple fw-bold">${s.weekend_explained_pct.toFixed(1)}%</span>
              <div class="progress-track" style="width: 100px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden;">
                <div style="width: ${Math.min(100, s.weekend_explained_pct * 2.5)}%; height: 100%; background: var(--purple-neon);"></div>
              </div>
            </div>
          </td>
          <td>
            <span class="dominant-pill ${isDominantRegion ? 'dom-city' : 'dom-wk'}">
              ${s.dominant_factor}
            </span>
          </td>
          <td class="text-center font-mono fw-bold text-amber">
            ${s.ratio}x
          </td>
          <td class="text-sm text-muted" style="max-width: 380px; line-height: 1.45;">
            ${expMap[s.metric_key] || ''}
          </td>
        </tr>
      `;
    }).join('');
  }
}

/**
 * Filter by Weekend
 */
function filterWeekend(wk) {
  currentWeekendFilter = wk;
  document.querySelectorAll('.pill-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.filter === wk);
  });
  renderMatrixTable();
}

/**
 * Real-time Search
 */
function handleSearch(term) {
  currentSearchTerm = term.toLowerCase().trim();
  renderMatrixTable();
}

/**
 * Toggle Weekend Progression Analysis Panel
 */
function toggleProgressionPanel() {
  const panel = document.getElementById('progression-panel');
  const btn = document.getElementById('btn-toggle-progression');
  if (!panel) return;

  const isHidden = panel.style.display === 'none';
  panel.style.display = isHidden ? 'block' : 'none';
  if (btn) {
    btn.classList.toggle('active', isHidden);
  }
}

/**
 * Column Header Sorting
 */
function sortTable(column) {
  if (currentSortColumn === column) {
    currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
  } else {
    currentSortColumn = column;
    currentSortDirection = (column === 'ly_max' || column === 'ly_top3' || column === 'ly_cutoff' || column === 'ly_median' || column === 'hist_count' || column === 'capacity') ? 'desc' : 'asc';
  }

  // Update table header sort indicators
  document.querySelectorAll('.sort-icon').forEach(icon => {
    icon.textContent = '';
  });
  const activeIcon = document.getElementById(`sort-${column}`);
  if (activeIcon) {
    activeIcon.textContent = currentSortDirection === 'asc' ? '▲' : '▼';
  }

  renderMatrixTable();
}

/**
 * Helper: Extract metric value for sorting
 */
function getSortValue(e, column) {
  const hist = e.venue_history || {};
  const past = hist.past_events || [];
  const bench = hist.benchmark || {};
  const ly = past.find(p => p.season_year === 2025);
  const lyM = ly ? ly.metrics : null;

  switch (column) {
    case 'weekend':
      return e.weekend || 0;
    case 'date':
      return e.date || '';
    case 'venue_name':
      return (e.venue_name || '').toLowerCase();
    case 'city':
      return (e.city || '').toLowerCase();
    case 'capacity':
      return e.capacity || 0;
    case 'ly_max':
      return lyM && lyM.max_score ? lyM.max_score : (bench.all_time_venue_max || -1);
    case 'ly_top3':
      return lyM && lyM.top3_avg ? lyM.top3_avg : (bench.avg_venue_top3 || -1);
    case 'ly_median':
      return lyM && lyM.median_score ? lyM.median_score : (bench.avg_venue_median || -1);
    case 'ly_cutoff':
      return lyM && lyM.advancement_cutoff ? lyM.advancement_cutoff : (bench.avg_advancement_cutoff || -1);
    case 'hist_count':
      return past.length || 0;
    default:
      return 0;
  }
}

/**
 * Render Master Matrix Table
 */
function renderMatrixTable() {
  const data = window.BIOGLOW_DATA;
  if (!data || !data.bioglow_events) return;

  const tbody = document.getElementById('matrix-tbody');
  if (!tbody) return;

  let events = [...data.bioglow_events];

  // 1. Filter
  events = events.filter(e => {
    if (currentWeekendFilter !== 'all' && String(e.weekend) !== currentWeekendFilter) {
      return false;
    }
    if (currentSearchTerm) {
      const q = currentSearchTerm;
      const haystack = `${e.name} ${e.venue_name} ${e.city}`.toLowerCase();
      if (!haystack.includes(q)) return false;
    }
    return true;
  });

  // 2. Sort
  events.sort((a, b) => {
    const valA = getSortValue(a, currentSortColumn);
    const valB = getSortValue(b, currentSortColumn);

    let comparison = 0;
    if (typeof valA === 'string' && typeof valB === 'string') {
      comparison = valA.localeCompare(valB);
    } else {
      comparison = valA < valB ? -1 : (valA > valB ? 1 : 0);
    }
    return currentSortDirection === 'asc' ? comparison : -comparison;
  });

  // Update row counter
  const rowCounter = document.getElementById('table-row-count');
  if (rowCounter) {
    rowCounter.textContent = `Showing ${events.length} of ${data.bioglow_events.length} Tournaments`;
  }

  tbody.innerHTML = '';

  if (events.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="12" style="text-align: center; padding: 3rem; color: var(--text-dim);">
          No tournaments matching current filter or search criteria.
        </td>
      </tr>
    `;
    return;
  }

  // 3. Build Rows
  events.forEach((e, idx) => {
    const hist = e.venue_history || {};
    const past = hist.past_events || [];
    const bench = hist.benchmark || {};
    const ly = past.find(p => p.season_year === 2025);
    const lyM = ly ? ly.metrics : null;

    // Date formatting (timezone-safe)
    let dayName = '', monthDay = '';
    if (e.date) {
      const parts = e.date.split("T")[0].split("-");
      if (parts.length === 3) {
        const d = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
        dayName = d.toLocaleDateString('en-US', { weekday: 'short' });
        monthDay = String(d.getMonth() + 1).padStart(2, '0') + '/' + String(d.getDate()).padStart(2, '0');
      }
    }

    // Weekend tag
    const wkClass = `week-${e.weekend}`;
    const wkBadge = `<span class="table-wk-badge ${wkClass}">W${e.weekend}</span>`;

    // Last year event badge
    let lyBadgeHtml = '';
    if (ly) {
      const lyDateStr = ly.date ? ly.date.slice(5) : '';
      const wkTag = ly.weekend ? `<span class="table-wk-badge-sm week-${ly.weekend}">第${ly.weekend}周末 (W${ly.weekend})</span>` : '';
      lyBadgeHtml = `
        <div class="ly-cell-wrap">
          ${wkTag}
          <button class="ly-link-badge week-${ly.weekend}" onclick="event.stopPropagation(); openEventModal(${ly.id})" title="查看 2025 详情">
            2025 #${ly.id} (${lyDateStr}) ↗
          </button>
        </div>
      `;
    } else if (past.length > 0) {
      const p0 = past[0];
      const pDateStr = p0.date ? p0.date.slice(5) : '';
      const wkJTag = p0.weekend ? `<span class="table-wk-badge-sm week-${p0.weekend}">第${p0.weekend}周末</span>` : '';
      lyBadgeHtml = `
        <div class="ly-cell-wrap">
          ${wkJTag}
          <button class="ly-link-badge prior" onclick="event.stopPropagation(); openEventModal(${p0.id})" title="查看往年详情">
            ${p0.season_year} #${p0.id} (${pDateStr}) ↗
          </button>
        </div>
      `;
    } else {
      lyBadgeHtml = `<span class="new-venue-tag">新赛场 (New)</span>`;
    }

    // Metric values
    const maxScore = lyM && lyM.max_score ? `<strong class="text-cyan font-bold">${lyM.max_score}</strong>` : (bench.all_time_venue_max ? `<span class="text-cyan font-bold">${bench.all_time_venue_max}*</span>` : '—');
    const top3Score = lyM && lyM.top3_avg ? `<strong>${lyM.top3_avg}</strong>` : (bench.avg_venue_top3 ? `~${bench.avg_venue_top3}*` : '—');
    const medianScore = lyM && lyM.median_score ? `${lyM.median_score}` : (bench.avg_venue_median ? `~${bench.avg_venue_median}*` : '—');

    // Cutoff with Competition Intensity Badge
    let cutoffHtml = '—';
    if (lyM && lyM.advancement_cutoff) {
      const cut = lyM.advancement_cutoff;
      let badgeClass = 'cut-moderate';
      if (cut >= 300) badgeClass = 'cut-high';
      else if (cut < 250) badgeClass = 'cut-friendly';

      cutoffHtml = `
        <div class="cutoff-cell">
          <span class="cutoff-badge ${badgeClass}">${cut} pts</span>
        </div>
      `;
    } else if (bench.avg_advancement_cutoff) {
      cutoffHtml = `
        <div class="cutoff-cell">
          <span class="cutoff-badge cut-moderate">~${bench.avg_advancement_cutoff}*</span>
        </div>
      `;
    }

    const isExpanded = expandedRowIds.has(e.id);
    const expandBtnIcon = isExpanded ? '▲' : '▼';
    const expandBtnText = isExpanded ? '收起' : '历年对比';

    // Main Row
    const tr = document.createElement('tr');
    tr.className = `matrix-row ${isExpanded ? 'row-expanded' : ''}`;
    tr.id = `row-${e.id}`;
    tr.onclick = () => toggleRowExpand(e.id);

    tr.innerHTML = `
      <td>${wkBadge}</td>
      <td>
        <div class="date-cell">
          <span class="date-m-d">${monthDay}</span>
          <span class="date-w-d">${dayName}</span>
        </div>
      </td>
      <td>
        <div class="venue-cell">
          <span class="venue-cell-name">${e.venue_name}</span>
          <span class="venue-cell-tid">Event #${e.id}</span>
        </div>
      </td>
      <td><span class="city-name-cell">${e.city}</span></td>
      <td class="text-center font-mono">${e.capacity || 18}</td>
      <td class="text-center">${lyBadgeHtml}</td>
      <td class="text-right">${maxScore}</td>
      <td class="text-right font-mono">${top3Score}</td>
      <td class="text-right font-mono">${medianScore}</td>
      <td class="text-right">${cutoffHtml}</td>
      <td class="text-center">
        <span class="hist-count-badge">${past.length} 届</span>
      </td>
      <td class="text-center" onclick="event.stopPropagation();">
        <div class="row-actions">
          <button class="btn-expand-row" onclick="toggleRowExpand(${e.id})">
            ${expandBtnText} ${expandBtnIcon}
          </button>
          ${ly ? `
            <button class="btn-quick-open" onclick="openEventModal(${ly.id})" title="打开 2025 完整赛报">
              📊 2025报表
            </button>
          ` : ''}
        </div>
      </td>
    `;
    tbody.appendChild(tr);

    // Expandable Sub-Row (Historical Comparison Accordion)
    if (isExpanded) {
      const subTr = document.createElement('tr');
      subTr.className = 'sub-row-accordion';
      subTr.id = `subrow-${e.id}`;

      subTr.innerHTML = `
        <td colspan="12">
          <div class="subrow-content">
            <div class="subrow-header">
              <div class="subrow-title">
                <span class="subrow-icon">🏛️</span>
                <strong>${e.venue_name} (${e.city}) 历年预选赛战绩与指标对比</strong>
              </div>
              <div class="subrow-close" onclick="toggleRowExpand(${e.id})">收起 ✕</div>
            </div>

            ${past.length === 0 ? `
              <div class="no-hist-message">
                该赛场为 2026 新增赛区，暂无往年同址预选赛直接数据。可参考同区域/同周末相近学校的表现基准。
              </div>
            ` : `
              <div class="subrow-cards-grid">
                ${past.map(p => {
                  const m = p.metrics || {};
                  return `
                    <div class="hist-card">
                      <div class="hist-card-head">
                        <span class="hist-card-season">${p.season}</span>
                        <span class="hist-card-wk">${p.weekend_label}</span>
                      </div>
                      <div class="hist-card-name" title="${p.name}">${p.name}</div>
                      <div class="hist-card-date">
                        📅 日期: <strong>${p.date}</strong> <span class="table-wk-badge-sm week-${p.weekend}">第${p.weekend}个周末 (${p.weekend_label})</span> • 参赛队: ${m.scored_teams || 'N/A'}
                      </div>

                      <div class="hist-card-metrics">
                        <div class="h-m-box">
                          <span class="h-val text-cyan">${m.max_score || '—'}</span>
                          <span class="h-lbl">最高分</span>
                        </div>
                        <div class="h-m-box">
                          <span class="h-val text-purple">${m.top3_avg || '—'}</span>
                          <span class="h-lbl">前三均分</span>
                        </div>
                        <div class="h-m-box">
                          <span class="h-val text-amber">${m.advancement_cutoff ? `${m.advancement_cutoff}` : '—'}</span>
                          <span class="h-lbl">晋级底线</span>
                        </div>
                        <div class="h-m-box">
                          <span class="h-val">${m.median_score || '—'}</span>
                          <span class="h-lbl">中位数</span>
                        </div>
                      </div>

                      <div class="hist-card-foot">
                        <button class="btn-view-hist-event" onclick="openEventModal(${p.id})">
                          <span>查看该届完整赛报与榜单 ↗</span>
                        </button>
                      </div>
                    </div>
                  `;
                }).join('')}
              </div>
            `}
          </div>
        </td>
      `;
      tbody.appendChild(subTr);
    }
  });
}

/**
 * Toggle Row Accordion
 */
function toggleRowExpand(eventId) {
  if (expandedRowIds.has(eventId)) {
    expandedRowIds.delete(eventId);
  } else {
    expandedRowIds.add(eventId);
  }
  renderMatrixTable();
}

/**
 * Open Event Detail Modal / Slide-over Drawer
 */
function openEventModal(eventId) {
  const data = window.BIOGLOW_DATA;
  if (!data || !data.events_by_id) return;

  const event = data.events_by_id[eventId];
  if (!event) {
    console.error('Event not found:', eventId);
    return;
  }

  const modal = document.getElementById('event-modal');
  const mName = document.getElementById('modal-event-name');
  const mMeta = document.getElementById('modal-event-meta');
  const mBadges = document.getElementById('modal-badges');
  const mKpiBar = document.getElementById('modal-kpi-bar');
  const mScoresCount = document.getElementById('modal-scores-count');
  const mAwardsCount = document.getElementById('modal-awards-count');
  const mScoresTbody = document.getElementById('modal-scores-tbody');
  const mAwardsGrid = document.getElementById('modal-awards-grid');
  const mRoundAnalysis = document.getElementById('modal-round-analysis');
  const mOfficialLink = document.getElementById('modal-official-link');

  // Header info
  mName.textContent = event.name;
  mMeta.innerHTML = `📅 <strong>${event.date}</strong> <span class="table-wk-badge-sm week-${event.weekend}">第${event.weekend}个周末 (${event.weekend_label})</span> &nbsp;•&nbsp; 📍 <strong>${event.venue_name}</strong> (${event.city}) &nbsp;•&nbsp; 🏆 <strong>${event.season}</strong>`;

  // Badges
  mBadges.innerHTML = `
    <span class="city-pill">${event.weekend_label}</span>
    <span class="city-pill">Season ${event.season_year}</span>
    <span class="adv-badge">ID #${event.id}</span>
  `;

  // Official Link
  mOfficialLink.href = `https://mylumi.playingatlearning.org${event.website_uri || `/en/event/${event.id}/`}`;

  const metrics = event.metrics || {};
  const scoresList = metrics.scores_list || [];
  const awardsList = metrics.awards_list || [];

  mScoresCount.textContent = scoresList.length;
  mAwardsCount.textContent = awardsList.length;

  // KPI Bar
  mKpiBar.innerHTML = `
    <div class="m-kpi-box">
      <div class="m-val text-cyan">${metrics.max_score || '—'}</div>
      <div class="m-lbl">单场最高分</div>
    </div>
    <div class="m-kpi-box">
      <div class="m-val text-purple">${metrics.top3_avg || '—'}</div>
      <div class="m-lbl">前三均分</div>
    </div>
    <div class="m-kpi-box">
      <div class="m-val">${metrics.median_score || '—'}</div>
      <div class="m-lbl">中位数</div>
    </div>
    <div class="m-kpi-box">
      <div class="m-val">${metrics.mean_score || '—'}</div>
      <div class="m-lbl">平均分</div>
    </div>
    <div class="m-kpi-box">
      <div class="m-val text-amber">${metrics.advancement_cutoff ? `${metrics.advancement_cutoff} pts` : '—'}</div>
      <div class="m-lbl">晋级底线分</div>
    </div>
    <div class="m-kpi-box">
      <div class="m-val text-emerald">${metrics.advancement_count || 0}</div>
      <div class="m-lbl">晋级队数</div>
    </div>
  `;

  // Scores Table
  mScoresTbody.innerHTML = '';
  if (scoresList.length === 0) {
    mScoresTbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-dim); padding: 2.5rem;">该场比赛未录入单轮具体得分数据。</td></tr>`;
  } else {
    scoresList.forEach(s => {
      const tr = document.createElement('tr');
      const isAdv = s.advancing;
      const isWait = s.waitlist;
      let statusHtml = '<span style="color: var(--text-dim); font-size: 0.78rem;">参评</span>';
      if (isAdv) {
        statusHtml = '<span class="adv-badge">✓ 晋级 Champs</span>';
      } else if (isWait) {
        statusHtml = '<span class="wait-badge">候补名单</span>';
      }

      tr.innerHTML = `
        <td><strong>${s.ordinal || s.ranking || '—'}</strong></td>
        <td><span style="font-family: var(--font-heading); font-weight: 700; color: var(--cyan-neon);">#${s.team_number}</span></td>
        <td><strong>${s.team_name}</strong></td>
        <td><strong class="text-cyan" style="font-size: 1rem;">${s.highest_score}</strong></td>
        <td>${s.round_1 !== null ? s.round_1 : '—'}</td>
        <td>${s.round_2 !== null ? s.round_2 : '—'}</td>
        <td>${s.round_3 !== null ? s.round_3 : '—'}</td>
        <td>${statusHtml}</td>
      `;
      mScoresTbody.appendChild(tr);
    });
  }

  // Awards Grid
  mAwardsGrid.innerHTML = '';
  if (awardsList.length === 0) {
    mAwardsGrid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: var(--text-dim); padding: 2.5rem;">暂无公开奖项数据。</div>`;
  } else {
    awardsList.forEach(a => {
      const isChamp = a.name.toLowerCase().includes('champion');
      const card = document.createElement('div');
      card.className = `award-card ${isChamp ? 'champion' : ''}`;
      card.innerHTML = `
        <div class="award-title">${isChamp ? '🏆 ' : '🎖️ '}${a.name}</div>
        <div class="award-team">队伍 #${a.team_number} - ${a.team_name}</div>
        <div class="award-cat">${a.category} 奖项</div>
      `;
      mAwardsGrid.appendChild(card);
    });
  }

  // Round Analysis Tab
  const rAvg = metrics.round_averages || [0, 0, 0];
  const dist = metrics.distribution || {};
  mRoundAnalysis.innerHTML = `
    <div style="margin-bottom: 2rem;">
      <h4 style="font-family: var(--font-heading); margin-bottom: 1rem;">各轮次（Round 1~3）平均得分递进</h4>
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem;">
        <div class="m-kpi-box">
          <div class="m-val">${rAvg[0] || '—'}</div>
          <div class="m-lbl">第一轮平均</div>
        </div>
        <div class="m-kpi-box">
          <div class="m-val text-cyan">${rAvg[1] || '—'}</div>
          <div class="m-lbl">第二轮平均</div>
        </div>
        <div class="m-kpi-box">
          <div class="m-val text-emerald">${rAvg[2] || '—'}</div>
          <div class="m-lbl">第三轮平均</div>
        </div>
      </div>
      <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.6;">
        各队通常在第二、三轮得分明显上升，得益于场地光线和摩擦力适应后程序的微调。
      </p>
    </div>

    <div>
      <h4 style="font-family: var(--font-heading); margin-bottom: 1rem;">最高得分区间分布</h4>
      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem;">
        <div class="m-kpi-box">
          <div class="m-val">${dist['<200'] || 0}</div>
          <div class="m-lbl">&lt; 200 分</div>
        </div>
        <div class="m-kpi-box">
          <div class="m-val">${dist['200-299'] || 0}</div>
          <div class="m-lbl">200 - 299 分</div>
        </div>
        <div class="m-kpi-box">
          <div class="m-val text-cyan">${dist['300-399'] || 0}</div>
          <div class="m-lbl">300 - 399 分</div>
        </div>
        <div class="m-kpi-box">
          <div class="m-val text-purple">${dist['400+'] || 0}</div>
          <div class="m-lbl">400+ 分 (强队梯队)</div>
        </div>
      </div>
    </div>
  `;

  // Default to scores tab
  switchModalTab('scores');

  // Open modal
  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function switchModalTab(tabKey) {
  document.querySelectorAll('.modal-tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  const btn = document.getElementById(`modal-tab-${tabKey}`);
  if (btn) btn.classList.add('active');

  document.querySelectorAll('.modal-tab-content').forEach(content => {
    content.classList.remove('active');
  });
  const target = document.getElementById(`modal-content-${tabKey}`);
  if (target) target.classList.add('active');
}

function closeModal() {
  const modal = document.getElementById('event-modal');
  if (modal) modal.classList.remove('open');
  document.body.style.overflow = 'auto';
}

function closeModalOnBackdrop(e) {
  if (e.target.id === 'event-modal') {
    closeModal();
  }
}
