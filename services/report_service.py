import os
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from config.app_config import AppConfig
from database.db_manager import db_manager
from utils.logger import get_logger
from utils.helpers import format_file_size, format_timestamp

class ReportService:
    def __init__(self):
        self.logger = get_logger('ReportService')
    
    def generate_report(self, 
                        log_ids: Optional[List[int]] = None,
                        report_type: str = 'recovery',
                        include_details: bool = True) -> Dict[str, Any]:
        logs = db_manager.get_operation_logs(limit=10000)
        
        if log_ids:
            target_logs = [l for l in logs if l.get('id') in log_ids]
        else:
            target_logs = logs
        
        report = {
            'report_info': {
                'type': report_type,
                'generated_at': datetime.now().isoformat(),
                'version': AppConfig.APP_VERSION,
                'total_records': len(target_logs)
            },
            'summary': self._generate_summary(target_logs),
            'operations': []
        }
        
        if include_details:
            for log in target_logs:
                report['operations'].append(self._format_log_entry(log))
        
        self.logger.info(f"生成报告: {len(target_logs)} 条记录")
        return report
    
    def _generate_summary(self, logs: List[Dict]) -> Dict[str, Any]:
        summary = {
            'total_operations': len(logs),
            'by_type': {},
            'by_risk': {},
            'by_status': {
                'recovered': 0,
                'pending': 0
            },
            'total_size': 0
        }
        
        for log in logs:
            op_type = log.get('operation_type', 'UNKNOWN')
            summary['by_type'][op_type] = summary['by_type'].get(op_type, 0) + 1
            
            risk = log.get('risk_level', 'LOW')
            summary['by_risk'][risk] = summary['by_risk'].get(risk, 0) + 1
            
            if log.get('is_recovered'):
                summary['by_status']['recovered'] += 1
            else:
                summary['by_status']['pending'] += 1
            
            summary['total_size'] += log.get('file_size', 0)
        
        summary['total_size_formatted'] = format_file_size(summary['total_size'])
        
        return summary
    
    def _format_log_entry(self, log: Dict) -> Dict[str, Any]:
        op_type = log.get('operation_type', 'UNKNOWN')
        op_info = AppConfig.OPERATION_TYPES.get(op_type, {'name': op_type})
        
        risk_level = log.get('risk_level', 'LOW')
        risk_info = AppConfig.RISK_LEVELS.get(risk_level, {'name': risk_level, 'color': '#ffffff'})
        
        return {
            'id': log.get('id'),
            'operation_type': op_type,
            'operation_name': op_info['name'],
            'file_name': log.get('file_name'),
            'file_path': log.get('file_path'),
            'file_size': log.get('file_size'),
            'file_size_formatted': format_file_size(log.get('file_size', 0)),
            'old_path': log.get('old_path'),
            'new_path': log.get('new_path'),
            'risk_level': risk_level,
            'risk_name': risk_info['name'],
            'risk_color': risk_info['color'],
            'impact_score': log.get('impact_score'),
            'has_backup': bool(log.get('has_backup')),
            'description': log.get('description'),
            'operation_time': format_timestamp(log.get('operation_time', 0)),
            'operation_timestamp': log.get('operation_time'),
            'is_recovered': bool(log.get('is_recovered')),
            'recovered_at': format_timestamp(log.get('recovered_at')) if log.get('recovered_at') else None
        }
    
    def export_to_json(self, report: Dict, file_path: str) -> bool:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            self.logger.info(f"JSON报告已导出: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"导出JSON报告失败: {e}")
            return False
    
    def export_to_csv(self, report: Dict, file_path: str) -> bool:
        try:
            operations = report.get('operations', [])
            
            if not operations:
                with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['报告类型', '生成时间', '记录总数'])
                    writer.writerow([
                        report.get('report_info', {}).get('type'),
                        report.get('report_info', {}).get('generated_at'),
                        report.get('report_info', {}).get('total_records')
                    ])
                return True
            
            fieldnames = [
                'ID', '操作类型', '文件名', '文件路径', '大小',
                '风险等级', '影响分数', '有备份', '操作时间',
                '状态', '描述', '原路径', '新路径'
            ]
            
            with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(fieldnames)
                
                for op in operations:
                    writer.writerow([
                        op.get('id'),
                        op.get('operation_name'),
                        op.get('file_name'),
                        op.get('file_path'),
                        op.get('file_size_formatted'),
                        op.get('risk_name'),
                        op.get('impact_score'),
                        '是' if op.get('has_backup') else '否',
                        op.get('operation_time'),
                        '已恢复' if op.get('is_recovered') else '待恢复',
                        op.get('description'),
                        op.get('old_path') or '-',
                        op.get('new_path') or '-'
                    ])
            
            self.logger.info(f"CSV报告已导出: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出CSV报告失败: {e}")
            return False
    
    def export_to_html(self, report: Dict, file_path: str) -> bool:
        try:
            html = self._generate_html_report(report)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            self.logger.info(f"HTML报告已导出: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出HTML报告失败: {e}")
            return False
    
    def _generate_html_report(self, report: Dict) -> str:
        report_info = report.get('report_info', {})
        summary = report.get('summary', {})
        operations = report.get('operations', [])
        
        risk_colors = {
            'LOW': '#4CAF50',
            'MEDIUM': '#FF9800',
            'HIGH': '#F44336',
            'CRITICAL': '#9C27B0'
        }
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件恢复报告 - {AppConfig.APP_NAME}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #007acc 0%, #1177bb 100%);
            color: white;
            padding: 30px;
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header p {{ font-size: 14px; opacity: 0.9; }}
        .content {{ padding: 30px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{
            font-size: 20px;
            color: #007acc;
            border-bottom: 2px solid #007acc;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        .summary-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #007acc;
        }}
        .summary-card .label {{
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: bold;
            color: #333;
        }}
        tr:hover {{ background: #f8f9fa; }}
        .risk-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            color: white;
        }}
        .status-recovered {{ color: #4CAF50; font-weight: bold; }}
        .status-pending {{ color: #F44336; font-weight: bold; }}
        .footer {{
            background: #f8f9fa;
            padding: 20px 30px;
            text-align: center;
            color: #666;
            font-size: 12px;
            border-top: 1px solid #eee;
        }}
        .path-cell {{
            font-family: 'Consolas', monospace;
            font-size: 12px;
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📄 文件恢复报告</h1>
            <p>生成时间: {report_info.get('generated_at')} | 报告版本: {report_info.get('version')}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>📊 统计概览</h2>
                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="value">{summary.get('total_operations', 0)}</div>
                        <div class="label">总操作数</div>
                    </div>
                    <div class="summary-card">
                        <div class="value">{summary.get('by_status', {{}}).get('recovered', 0)}</div>
                        <div class="label">已恢复</div>
                    </div>
                    <div class="summary-card">
                        <div class="value">{summary.get('by_status', {{}}).get('pending', 0)}</div>
                        <div class="label">待恢复</div>
                    </div>
                    <div class="summary-card">
                        <div class="value">{summary.get('total_size_formatted', '0 B')}</div>
                        <div class="label">总大小</div>
                    </div>
                </div>
            </div>
"""
        
        by_type = summary.get('by_type', {})
        by_risk = summary.get('by_risk', {})
        
        if by_type or by_risk:
            html += """
            <div class="section">
                <h2>📈 分布统计</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
"""
            
            if by_type:
                html += """
                    <div>
                        <h3 style="margin-bottom: 15px; color: #555;">按操作类型</h3>
                        <table>
                            <tr><th>类型</th><th>数量</th></tr>
"""
                for op_type, count in by_type.items():
                    op_info = AppConfig.OPERATION_TYPES.get(op_type, {'name': op_type})
                    html += f"<tr><td>{op_info['name']}</td><td>{count}</td></tr>\n"
                html += """
                        </table>
                    </div>
"""
            
            if by_risk:
                html += """
                    <div>
                        <h3 style="margin-bottom: 15px; color: #555;">按风险等级</h3>
                        <table>
                            <tr><th>风险等级</th><th>数量</th></tr>
"""
                for risk, count in by_risk.items():
                    risk_info = AppConfig.RISK_LEVELS.get(risk, {'name': risk, 'color': '#888'})
                    html += f"<tr><td><span class='risk-badge' style='background: {risk_info['color']}'>{risk_info['name']}</span></td><td>{count}</td></tr>\n"
                html += """
                        </table>
                    </div>
"""
            
            html += """
                </div>
            </div>
"""
        
        if operations:
            html += f"""
            <div class="section">
                <h2>📋 操作详情 ({len(operations)} 条记录)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>操作类型</th>
                            <th>文件名</th>
                            <th>文件路径</th>
                            <th>大小</th>
                            <th>风险</th>
                            <th>操作时间</th>
                            <th>状态</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            
            for op in operations[:100]:
                risk_color = risk_colors.get(op.get('risk_level', 'LOW'), '#888')
                status_class = 'status-recovered' if op.get('is_recovered') else 'status-pending'
                status_text = '已恢复' if op.get('is_recovered') else '待恢复'
                
                html += f"""
                        <tr>
                            <td>{op.get('id')}</td>
                            <td>{op.get('operation_name')}</td>
                            <td>{op.get('file_name')}</td>
                            <td class="path-cell" title="{op.get('file_path')}">{op.get('file_path')}</td>
                            <td>{op.get('file_size_formatted')}</td>
                            <td><span class="risk-badge" style="background: {risk_color}">{op.get('risk_name')}</span></td>
                            <td>{op.get('operation_time')}</td>
                            <td class="{status_class}">{status_text}</td>
                        </tr>
"""
            
            if len(operations) > 100:
                html += f"""
                        <tr>
                            <td colspan="8" style="text-align: center; color: #888;">
                                ... 还有 {len(operations) - 100} 条记录
                            </td>
                        </tr>
"""
            
            html += """
                    </tbody>
                </table>
            </div>
"""
        
        html += f"""
        </div>
        
        <div class="footer">
            <p>此报告由 {AppConfig.APP_NAME} v{AppConfig.APP_VERSION} 生成</p>
            <p>© 2024 File Recovery Pro. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def auto_export_report(self, log_ids: List[int], output_dir: str) -> Dict[str, str]:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report = self.generate_report(log_ids)
        
        outputs = {}
        
        json_path = os.path.join(output_dir, f"recovery_report_{timestamp}.json")
        if self.export_to_json(report, json_path):
            outputs['json'] = json_path
        
        csv_path = os.path.join(output_dir, f"recovery_report_{timestamp}.csv")
        if self.export_to_csv(report, csv_path):
            outputs['csv'] = csv_path
        
        html_path = os.path.join(output_dir, f"recovery_report_{timestamp}.html")
        if self.export_to_html(report, html_path):
            outputs['html'] = html_path
        
        return outputs

report_service = ReportService()
