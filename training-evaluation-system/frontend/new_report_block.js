    report: {
        data: {
            trainings: [],
            selectedTraining: null,
            studentReports: [],
            filteredReports: [],
            commonProblems: [],
            abnormalStudents: [],
            generatedReports: [],
            warningThreshold: 60,
            selectedStudent: null,
            selectedSubmissionId: null,
            searchQuery: '',
            currentFollowUpNote: '',
            reviewModalOpen: false,
            abnormalModalOpen: false,
            editingScore: null,
            editingComment: ''
        },
        async loadTrainings() {
            try {
                const res = await api.get('/courses/teacher/mine/trainings');
                this.data.trainings = (res.trainings || []).filter(t => t.status !== 'archived');
                if (this.data.trainings.length && !this.data.selectedTraining) {
                    this.data.selectedTraining = this.data.trainings[0];
                }
            } catch (e) {
                console.warn('获取实训列表失败:', e);
                this.data.trainings = [];
            }
        },
        async loadStudentReports() {
            if (!this.data.selectedTraining) return;
            try {
                const res = await api.get(`/report/training/${this.data.selectedTraining.id}/data`);
                this.data.studentReports = res.submissions || [];
                this.applySearch();
            } catch (e) {
                console.warn('获取学生报告失败:', e);
                this.data.studentReports = [];
                this.data.filteredReports = [];
            }
        },
        async loadCommonProblems() {
            if (!this.data.selectedTraining) return;
            try {
                const res = await api.get(`/report/training/${this.data.selectedTraining.id}/common-problems`);
                this.data.commonProblems = Array.isArray(res) ? res : (res.problems || []);
            } catch (e) {
                console.warn('获取共性问题失败:', e);
                this.data.commonProblems = [];
            }
        },
        async loadAbnormalStudents() {
            if (!this.data.selectedTraining) return;
            try {
                const res = await api.post(`/report/training/${this.data.selectedTraining.id}/abnormal-students`, {
                    threshold: this.data.warningThreshold
                });
                this.data.abnormalStudents = Array.isArray(res) ? res : (res.students || []);
            } catch (e) {
                console.warn('获取异常学生失败:', e);
                this.data.abnormalStudents = [];
            }
        },
        async loadGeneratedReports() {
            if (!this.data.selectedTraining) return;
            try {
                const res = await api.get(`/report/list/${this.data.selectedTraining.id}`);
                this.data.generatedReports = res || [];
            } catch (e) {
                console.warn('获取报告列表失败:', e);
                this.data.generatedReports = [];
            }
        },
        async viewStudentDetail(submissionId) {
            try {
                const res = await api.get(`/report/student/${submissionId}`);
                const student = this.normalizeStudentDetail(res);
                this.data.selectedStudent = student;
                this.data.selectedSubmissionId = submissionId;
                this.data.currentFollowUpNote = student.follow_up_note || '';
                this.render();
            } catch (e) {
                toast.error('加载学生报告失败: ' + (e.message || '未知错误'));
            }
        },
        normalizeStudentDetail(raw) {
            const submission = raw.submission || {};
            const scores = raw.scores || {};
            const annotations = (raw.code_annotations || []).map(a => ({
                line: a.line_number || a.line || 0,
                type: a.type || 'suggestion',
                message: a.message || '',
                suggestion: a.suggestion || ''
            }));
            const indicators = (scores.indicator_scores || []).map(i => ({
                dimension: i.name,
                score: i.score,
                max_score: i.max_score || 100,
                comment: i.reason || ''
            }));
            return {
                submission_id: submission.id,
                student_id: submission.student_id,
                student_name: submission.student_name,
                training_title: (raw.training || {}).title,
                final_score: scores.final_score,
                ai_score: scores.ai_total_score,
                teacher_score: scores.teacher_score,
                ai_comment: scores.overall_comment,
                teacher_comment: raw.teacher_comment,
                follow_up_note: raw.follow_up_note,
                dimension_scores: indicators,
                code_annotations: annotations,
                status_label: submission.status_label,
                document_status: submission.document_status
            };
        },
        getDimensionScore(report, dimName) {
            const scores = report.dimension_scores || {};
            if (scores[dimName] !== undefined && scores[dimName] !== null) return scores[dimName];
            const indicators = report.indicator_scores || [];
            const found = indicators.find(i => i.name && i.name.includes(dimName));
            return found ? found.score : null;
        },
        getAnnotationCount(report) {
            const detail = report.evaluation_detail || {};
            const annotations = detail.code_annotations || [];
            const aiScores = detail.ai_scores || [];
            if (annotations.length) return annotations.length;
            return aiScores.filter(s => {
                const reason = s.reason || '';
                return reason.includes('错误') || reason.includes('问题') || reason.includes('建议');
            }).length;
        },
        applySearch() {
            const q = (this.data.searchQuery || '').trim().toLowerCase();
            if (!q) {
                this.data.filteredReports = [...this.data.studentReports];
                return;
            }
            this.data.filteredReports = this.data.studentReports.filter(r =>
                (r.student_name && r.student_name.toLowerCase().includes(q)) ||
                (r.student_id && String(r.student_id).toLowerCase().includes(q))
            );
        },
        onSearchInput(value) {
            this.data.searchQuery = value;
            this.applySearch();
            this.render();
        },
        onSelectTraining(trainingId) {
            this.data.selectedTraining = this.data.trainings.find(t => String(t.id) === String(trainingId));
            this.data.selectedStudent = null;
            this.data.selectedSubmissionId = null;
            this.data.searchQuery = '';
            this.render();
        },
        async saveReview(submissionId, dimension, newScore, comment) {
            try {
                await api.post(`/evaluation/teacher-review/${submissionId}`, {
                    teacher_score: newScore,
                    teacher_comment: comment
                });
                toast.success('评分已保存，已同步存入学生成长档案');
                this.data.editingScore = null;
                this.data.editingComment = '';
                await this.loadStudentReports();
                if (this.data.selectedSubmissionId) {
                    await this.viewStudentDetail(this.data.selectedSubmissionId);
                } else {
                    this.render();
                }
            } catch (e) {
                toast.error('保存失败: ' + (e.message || '未知错误'));
            }
        },
        async addFollowNote(studentId, note) {
            try {
                await api.post(`/report/training/${this.data.selectedTraining.id}/follow-up`, {
                    student_id: studentId,
                    note: note
                });
                toast.success('跟进备注已添加');
                await this.loadAbnormalStudents();
            } catch (e) {
                toast.error('添加备注失败: ' + (e.message || '未知错误'));
            }
        },
        async saveCurrentFollowNote() {
            if (!this.data.selectedStudent) return;
            try {
                await api.post(`/evaluation/teacher-review/${this.data.selectedStudent.submission_id}`, {
                    teacher_comment: this.data.currentFollowUpNote
                });
                toast.success('跟进备注已保存');
                await this.loadStudentReports();
                await this.viewStudentDetail(this.data.selectedStudent.submission_id);
            } catch (e) {
                toast.error('保存失败: ' + (e.message || '未知错误'));
            }
        },
        async generateSingleReport(submissionId) {
            try {
                await api.post(`/report/generate/student/${submissionId}`);
                toast.success('报告生成成功');
                await this.loadGeneratedReports();
            } catch (e) {
                toast.error('生成报告失败: ' + (e.message || '未知错误'));
            }
        },
        async batchGenerateReports() {
            if (!this.data.selectedTraining) return;
            try {
                await api.post(`/report/batch-generate/${this.data.selectedTraining.id}`);
                toast.success('批量报告生成成功');
                await this.loadGeneratedReports();
            } catch (e) {
                toast.error('批量生成失败: ' + (e.message || '未知错误'));
            }
        },
        async batchExport(type) {
            if (!this.data.selectedTraining) return;
            if (!confirm(`确定批量导出全班${type === 'pdf' ? 'PDF' : 'Excel'}报告吗？`)) return;
            try {
                if (type === 'pdf') {
                    await this.batchGenerateReports();
                } else {
                    const res = await api.get(`/report/training/${this.data.selectedTraining.id}/data`);
                    const submissions = res.submissions || [];
                    const headers = ['学号', '姓名', 'AI评分', '教师评分', '最终评分', 'AI评阅状态', '文档状态'];
                    const rows = submissions.map(s => [
                        s.student_id || '', s.student_name || '', s.ai_total_score ?? '', s.teacher_score ?? '', s.final_score ?? '',
                        s.ai_review_status || '', s.document_status || ''
                    ].join(','));
                    const csv = '\uFEFF' + [headers.join(','), ...rows].join('\n');
                    this.downloadBlob(csv, `${this.data.selectedTraining.title}_全班成绩汇总.csv`, 'text/csv');
                }
                toast.success('批量导出完成');
            } catch (e) {
                toast.error('批量导出失败: ' + (e.message || '未知错误'));
            }
        },
        downloadBlob(content, filename, mimeType) {
            const blob = new Blob([content], { type: mimeType });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            window.URL.revokeObjectURL(url);
        },
        async exportProblems() {
            if (!this.data.selectedTraining) return;
            try {
                const resp = await fetch(`${API_BASE}/report/training/${this.data.selectedTraining.id}/export-problems`, {
                    headers: getAuthHeaders()
                });
                const blob = await resp.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `共性问题汇总_${this.data.selectedTraining.title}.csv`;
                a.click();
                window.URL.revokeObjectURL(url);
                toast.success('导出成功');
            } catch (e) {
                toast.error('导出失败: ' + (e.message || '未知错误'));
            }
        },
        getScoreColor(score) {
            if (score >= 90) return '#52C41A';
            if (score >= 80) return '#1677ff';
            if (score >= 60) return '#FAAD14';
            return '#FF4D4F';
        },
        getScoreLabel(score) {
            if (score >= 90) return '优秀';
            if (score >= 80) return '良好';
            if (score >= 60) return '及格';
            return '不及格';
        },
        getRingCircumference() {
            return 2 * Math.PI * 52;
        },
        getRingOffset(score) {
            const circumference = this.getRingCircumference();
            return circumference - (Math.min(score || 0, 100) / 100) * circumference;
        },
        openReviewModal() {
            if (!this.data.selectedStudent) return;
            this.data.reviewModalOpen = true;
            this.renderModals();
        },
        closeReviewModal() {
            this.data.reviewModalOpen = false;
            this.renderModals();
        },
        async submitReview() {
            const scoreInput = document.getElementById('review-teacher-score');
            const commentInput = document.getElementById('review-teacher-comment');
            const score = scoreInput ? parseFloat(scoreInput.value) : null;
            const comment = commentInput ? commentInput.value : '';
            if (isNaN(score)) {
                toast.error('请输入有效分数');
                return;
            }
            await this.saveReview(this.data.selectedStudent.submission_id, null, score, comment);
            this.closeReviewModal();
        },
        openAbnormalModal() {
            this.data.abnormalModalOpen = true;
            this.renderModals();
        },
        closeAbnormalModal() {
            this.data.abnormalModalOpen = false;
            this.renderModals();
        },
        async updateThreshold() {
            const input = document.getElementById('abnormal-threshold');
            const threshold = input ? parseInt(input.value) : NaN;
            if (!isNaN(threshold)) {
                this.data.warningThreshold = threshold;
                await this.loadAbnormalStudents();
                this.renderModals();
            }
        },
        showAddNote(studentId, studentName) {
            const note = prompt(`为 ${studentName} 添加跟进备注：`);
            if (note) {
                this.addFollowNote(studentId, note);
            }
        },
        renderScoreRing(student) {
            const score = student.final_score || 0;
            const color = this.getScoreColor(score);
            const circumference = this.getRingCircumference();
            const offset = this.getRingOffset(score);
            return `
                <div class="report-score-ring">
                    <svg viewBox="0 0 120 120">
                        <circle cx="60" cy="60" r="52" fill="none" stroke="#E5E6EB" stroke-width="10" />
                        <circle cx="60" cy="60" r="52" fill="none" stroke="${color}" stroke-width="10" stroke-linecap="round"
                            stroke-dasharray="${circumference}" stroke-dashoffset="${offset}" transform="rotate(-90 60 60)" />
                    </svg>
                    <div class="report-score-text">
                        <div class="report-score-number">${score}</div>
                        <div class="report-score-unit">分</div>
                    </div>
                </div>
            `;
        },
        renderDimensionBars(student) {
            const dims = ['逻辑结构', '代码规范', '功能实现'];
            const colors = ['#1677ff', '#52C41A', '#FAAD14'];
            return dims.map((dim, idx) => {
                const item = (student.dimension_scores || []).find(d => d.dimension && d.dimension.includes(dim));
                const score = item ? item.score : null;
                const max = item ? (item.max_score || 100) : 100;
                const percentage = score !== null && score !== undefined ? Math.round((score / max) * 100) : 0;
                return `
                    <div class="report-dimension-bar">
                        <div class="report-dimension-bar-header">
                            <span>${dim}</span>
                            <span>${score !== null && score !== undefined ? score : '-'}</span>
                        </div>
                        <div class="report-dimension-bar-track">
                            <div class="report-dimension-bar-fill" style="width:${percentage}%; background:${colors[idx]}"></div>
                        </div>
                    </div>
                `;
            }).join('');
        },
        renderStudentPanel() {
            const student = this.data.selectedStudent;
            if (!student) {
                return `
                    <div class="report-card">
                        <div class="report-card-body">
                            <div class="report-empty">请从左侧表格选择学生查看详细报告</div>
                        </div>
                    </div>
                `;
            }
            const annotationsHtml = (student.code_annotations || []).length ? student.code_annotations.map(a => `
                <div class="report-annotation ${a.type}">
                    <div class="report-annotation-title">
                        <span class="icon">${a.type === 'error' ? '❌' : a.type === 'warning' ? '⚠️' : '💡'}</span>
                        <span>错误点：第${a.line}行${a.type === 'error' ? '错误' : a.type === 'warning' ? '警告' : '建议'}</span>
                    </div>
                    <div class="report-annotation-content">${a.message}</div>
                    ${a.suggestion ? `<div class="report-annotation-suggestion"><strong>修改建议：</strong>${a.suggestion}</div>` : ''}
                </div>
            `).join('') : '<div class="report-empty">暂无代码批注</div>';

            return `
                <div class="report-card">
                    <div class="report-card-body">
                        <div class="report-student-header">
                            <div>
                                <h3>单学生完整AI评价报告</h3>
                                <p>${student.student_name || '--'} | ${student.student_id || '--'} | ${student.training_title || '--'}</p>
                            </div>
                            <button class="btn btn-primary btn-sm" onclick="views.report.openReviewModal()">人工复核</button>
                        </div>

                        <div class="report-score-overview">
                            ${this.renderScoreRing(student)}
                            <div class="report-dimension-bars">
                                ${this.renderDimensionBars(student)}
                            </div>
                        </div>

                        <div class="report-section">
                            <div class="report-section-title">AI综合评语</div>
                            <div class="report-comment-box">${student.ai_comment || '暂无AI综合评语'}</div>
                        </div>

                        <div class="report-section">
                            <div class="report-section-title">班级添加跟进备注</div>
                            <textarea class="report-textarea" id="current-follow-note" rows="2" placeholder="输入跟进备注，修改记录将同步存入学生成长档案...">${this.escapeHtml(this.data.currentFollowUpNote)}</textarea>
                            <div class="report-section-actions">
                                <button class="btn btn-primary btn-sm" onclick="views.report.saveCurrentFollowNote()">保存复核记录</button>
                            </div>
                        </div>

                        <div class="report-section">
                            <div class="report-section-title">代码逐段批注</div>
                            ${annotationsHtml}
                        </div>
                    </div>
                </div>
            `;
        },
        renderCommonProblemsPanel() {
            const problems = this.data.commonProblems.slice(0, 5);
            return `
                <div class="report-card report-common-problems">
                    <div class="report-card-body">
                        <div class="report-section-title">班级共性问题汇总</div>
                        ${problems.length ? problems.map(p => `
                            <div class="problem-item">
                                <div class="report-problem-info">
                                    <span class="report-problem-name">${p.keyword}</span>
                                    <span class="report-problem-count">${p.student_count}人</span>
                                </div>
                                <div class="report-problem-bar">
                                    <div class="report-problem-bar-fill" style="width:${Math.min(p.student_count * 10, 100)}%; background:${p.severity === 'high' ? '#FF4D4F' : p.severity === 'medium' ? '#FAAD14' : '#1677ff'}"></div>
                                </div>
                            </div>
                        `).join('') : '<div class="report-empty">暂无共性问题数据</div>'}
                        <div class="report-common-problems-actions">
                            <button class="btn btn-primary btn-sm" onclick="views.report.exportProblems()">导出课堂讲解汇总</button>
                        </div>
                    </div>
                </div>
            `;
        },
        renderReviewModal() {
            const student = this.data.selectedStudent;
            if (!this.data.reviewModalOpen || !student) return '';
            return `
                <div class="report-modal-backdrop show" onclick="views.report.closeReviewModal()"></div>
                <div class="report-modal show">
                    <div class="report-modal-header">
                        <h3>人工复核</h3>
                        <button class="report-modal-close" onclick="views.report.closeReviewModal()">&times;</button>
                    </div>
                    <div class="report-modal-body">
                        <div class="form-group">
                            <label>AI评分</label>
                            <input type="text" class="form-control" value="${student.ai_score != null ? student.ai_score : '--'}" readonly>
                        </div>
                        <div class="form-group">
                            <label>教师评分</label>
                            <input type="number" class="form-control" id="review-teacher-score" value="${student.teacher_score != null ? student.teacher_score : ''}" min="0" max="100" step="0.5">
                        </div>
                        <div class="form-group">
                            <label>复核备注</label>
                            <textarea class="form-control" id="review-teacher-comment" rows="4" placeholder="输入教师评语，将同步存入学生成长档案...">${this.escapeHtml(student.teacher_comment || '')}</textarea>
                        </div>
                    </div>
                    <div class="report-modal-footer">
                        <button class="btn btn-default" onclick="views.report.closeReviewModal()">取消</button>
                        <button class="btn btn-primary" onclick="views.report.submitReview()">提交复核</button>
                    </div>
                </div>
            `;
        },
        renderAbnormalModal() {
            if (!this.data.abnormalModalOpen) return '';
            const students = this.data.abnormalStudents;
            return `
                <div class="report-modal-backdrop show" onclick="views.report.closeAbnormalModal()"></div>
                <div class="report-modal report-abnormal-modal show">
                    <div class="report-modal-header">
                        <h3>异常学生重点关注清单</h3>
                        <button class="report-modal-close" onclick="views.report.closeAbnormalModal()">&times;</button>
                    </div>
                    <div class="report-modal-body">
                        <div class="report-abnormal-toolbar">
                            <span>预警阈值：</span>
                            <input type="number" id="abnormal-threshold" value="${this.data.warningThreshold}" min="0" max="100">
                            <span>分以下</span>
                            <button class="btn btn-default btn-sm" onclick="views.report.updateThreshold()">更新</button>
                        </div>
                        ${students.length ? `
                            <div class="report-table-wrapper">
                                <table class="report-table">
                                    <thead>
                                        <tr>
                                            <th>学号</th>
                                            <th>姓名</th>
                                            <th>最终得分</th>
                                            <th>AI评分</th>
                                            <th>跟进备注</th>
                                            <th>操作</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${students.map(s => `
                                            <tr>
                                                <td>${s.student_id || '--'}</td>
                                                <td>${s.student_name || '--'}</td>
                                                <td style="color:#FF4D4F; font-weight:600">${s.final_score != null ? s.final_score : '--'}</td>
                                                <td>${s.ai_total_score != null ? s.ai_total_score : '--'}</td>
                                                <td>${s.follow_note || '-'}</td>
                                                <td>
                                                    <button class="btn btn-text" onclick="views.report.viewStudentDetail(${s.id}); views.report.closeAbnormalModal()">查看报告</button>
                                                    <button class="btn btn-text" onclick="views.report.showAddNote(${s.student_id}, '${this.escapeHtml(s.student_name || '')}')">添加备注</button>
                                                </td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        ` : '<div class="report-empty">暂无低于预警阈值的学生</div>'}
                    </div>
                </div>
            `;
        },
        renderModals() {
            const modalContainer = document.getElementById('report-modal-container');
            if (modalContainer) {
                modalContainer.innerHTML = this.renderReviewModal() + this.renderAbnormalModal();
            }
        },
        escapeHtml(text) {
            if (text == null) return '';
            return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
        },
        render: async function() {
            const content = document.getElementById('page-content');
            content.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>加载中...</p></div>';

            await this.loadTrainings();
            if (this.data.selectedTraining) {
                await Promise.all([
                    this.loadStudentReports(),
                    this.loadCommonProblems(),
                    this.loadAbnormalStudents(),
                    this.loadGeneratedReports()
                ]);
            }

            if (this.data.studentReports.length && !this.data.selectedStudent && !this.data.selectedSubmissionId) {
                await this.viewStudentDetail(this.data.studentReports[0].id);
                return;
            }

            const trainingOptions = this.data.trainings.map(t =>
                `<option value="${t.id}" ${this.data.selectedTraining && this.data.selectedTraining.id === t.id ? 'selected' : ''}>${this.escapeHtml(t.title)}</option>`
            ).join('');
            const reports = this.data.filteredReports;

            content.innerHTML = `
                <div class="report-page-header">
                    <div>
                        <h2>AI评阅报告</h2>
                        <p>AI自动完成全班级实训评阅，集中展示智能评价结果，减少重复批改工作</p>
                    </div>
                    <button class="btn btn-warning" onclick="views.report.openAbnormalModal()">⚠️ 异常学生清单</button>
                </div>

                <div class="report-toolbar">
                    <div class="report-toolbar-left">
                        <input type="text" class="report-search" placeholder="搜索学生姓名/学号" value="${this.escapeHtml(this.data.searchQuery)}" oninput="views.report.onSearchInput(this.value)">
                        <select class="report-select" onchange="views.report.onSelectTraining(this.value)">
                            ${trainingOptions}
                        </select>
                    </div>
                    <div class="report-toolbar-right">
                        <button class="btn btn-primary" onclick="views.report.batchExport('pdf')">批量导出全部PDF</button>
                        <button class="btn btn-success" onclick="views.report.batchExport('excel')">批量导出全部Excel</button>
                    </div>
                </div>

                <div class="report-main-grid">
                    <div class="report-card">
                        <div class="report-card-body report-table-wrapper">
                            <table class="report-table">
                                <thead>
                                    <tr>
                                        <th>序号</th>
                                        <th>学号</th>
                                        <th>姓名</th>
                                        <th>总分</th>
                                        <th>逻辑结构</th>
                                        <th>代码规范</th>
                                        <th>功能实现</th>
                                        <th>批注</th>
                                        <th>AI评阅状态</th>
                                        <th>文档状态</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${reports.length ? reports.map((r, idx) => `
                                        <tr class="${this.data.selectedSubmissionId === r.id ? 'active' : ''}" onclick="views.report.viewStudentDetail(${r.id})">
                                            <td>${idx + 1}</td>
                                            <td>${r.student_id || '--'}</td>
                                            <td>${r.student_name || '--'}</td>
                                            <td class="score-cell" style="color:${this.getScoreColor(r.final_score || 0)}">${r.final_score != null ? r.final_score : '--'}</td>
                                            <td>${this.getDimensionScore(r, '逻辑结构') != null ? this.getDimensionScore(r, '逻辑结构') : '-'}</td>
                                            <td>${this.getDimensionScore(r, '代码规范') != null ? this.getDimensionScore(r, '代码规范') : '-'}</td>
                                            <td>${this.getDimensionScore(r, '功能实现') != null ? this.getDimensionScore(r, '功能实现') : '-'}</td>
                                            <td>${this.getAnnotationCount(r)}</td>
                                            <td><span class="tag ${r.status === 'evaluated' ? 'tag-success' : 'tag-info'}">${r.ai_review_status || (r.status === 'evaluated' ? '已评阅' : '未评阅')}</span></td>
                                            <td><span class="tag ${r.document_status === '已提交' ? 'tag-primary' : 'tag-info'}">${r.document_status || '未提交'}</span></td>
                                            <td>
                                                <button class="btn btn-text" onclick="event.stopPropagation(); views.report.viewStudentDetail(${r.id})">查看报告</button>
                                                <button class="btn btn-text" onclick="event.stopPropagation(); views.report.generateSingleReport(${r.id})">导出PDF</button>
                                            </td>
                                        </tr>
                                    `).join('') : '<tr><td colspan="11" class="report-empty">暂无数据</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div class="report-right-panel">
                        ${this.renderStudentPanel()}
                        ${this.renderCommonProblemsPanel()}
                    </div>
                </div>

                <div id="report-modal-container"></div>
            `;

            this.renderModals();
        },
        selectTraining(trainingId) {
            this.onSelectTraining(trainingId);
        },
        switchTab(tab) {
            // 保留旧接口，避免其他调用报错
            this.data.activeTab = tab;
        }
    },
