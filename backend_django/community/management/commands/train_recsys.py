from django.core.management.base import BaseCommand, CommandError

from community.recommendation import reset_recsys_service
from community.recsys_pipeline import (
    export_interactions_csv,
    get_recsys_paths,
    run_recsys_training,
    write_recsys_status,
)


class Command(BaseCommand):
    help = '从数据库导出交互数据并训练推荐模型（建议每天执行一次）'

    def add_arguments(self, parser):
        parser.add_argument('--trials', type=int, default=10)
        parser.add_argument('--val-ratio', type=float, default=0.1)
        parser.add_argument('--export-only', action='store_true')
        parser.add_argument('--min-rows', type=int, default=10)

    def handle(self, *args, **options):
        recsys_root, cache_dir, export_csv, model_path = get_recsys_paths()
        if not recsys_root.exists():
            raise CommandError(f'推荐系统目录不存在: {recsys_root}')

        row_count = export_interactions_csv(export_csv)
        if row_count == 0:
            self.stdout.write(self.style.WARNING('没有可导出的交互数据，跳过训练。'))
            write_recsys_status(
                {
                    'status': 'skipped',
                    'reason': 'no_interactions',
                    'exportRows': 0,
                }
            )
            return

        self.stdout.write(self.style.SUCCESS(f'已导出 {row_count} 条交互到: {export_csv}'))

        if options['export_only']:
            write_recsys_status(
                {
                    'status': 'export_only',
                    'exportRows': row_count,
                    'exportPath': str(export_csv),
                }
            )
            return

        min_rows = options['min_rows']
        if row_count < min_rows:
            self.stdout.write(
                self.style.WARNING(
                    f'导出样本仅 {row_count} 条，低于最小阈值 {min_rows}，跳过训练并保留旧模型。'
                )
            )
            write_recsys_status(
                {
                    'status': 'skipped',
                    'reason': 'too_few_rows',
                    'exportRows': row_count,
                    'minRows': min_rows,
                }
            )
            return

        trials = options['trials']
        val_ratio = options['val_ratio']
        self.stdout.write(f'开始训练推荐模型：trials={trials}, val_ratio={val_ratio}')

        try:
            run_recsys_training(
                recsys_root=recsys_root,
                export_csv=export_csv,
                cache_dir=cache_dir,
                trials=trials,
                val_ratio=val_ratio,
            )
        except Exception as exc:
            write_recsys_status(
                {
                    'status': 'failed',
                    'exportRows': row_count,
                    'trials': trials,
                    'valRatio': val_ratio,
                    'error': str(exc),
                }
            )
            raise CommandError(f'推荐训练失败: {exc}') from exc

        if not model_path.exists():
            write_recsys_status(
                {
                    'status': 'failed',
                    'exportRows': row_count,
                    'trials': trials,
                    'valRatio': val_ratio,
                    'error': f'model_not_found: {model_path}',
                }
            )
            raise CommandError(f'训练完成但未找到模型文件: {model_path}')

        reset_recsys_service()
        write_recsys_status(
            {
                'status': 'success',
                'exportRows': row_count,
                'trials': trials,
                'valRatio': val_ratio,
                'modelPath': str(model_path),
                'exportPath': str(export_csv),
            }
        )
        self.stdout.write(self.style.SUCCESS(f'训练完成，模型已更新: {model_path}'))
