import logging
import os
import sys

# Adiciona o diretório raiz ao path para permitir execução direta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import sqlalchemy
    from sqlalchemy import text, inspect
    from app.database import engine
    from app.models import Base
except ImportError:
    # Caso falte alguma dependência no ambiente de execução direta
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DatabaseMigrator")

class DatabaseMigrator:
    """
    Utilitário para garantir que o banco de dados físico esteja em sincronia
    com os modelos SQLAlchemy, adicionando colunas faltantes dinamicamente.
    """

    @staticmethod
    def migrate():
        logger.info("Iniciando verificação de esquema do banco de dados...")
        inspector = inspect(engine)
        
        with engine.connect() as conn:
            # 1. Obter todas as tabelas e colunas esperadas do SQLAlchemy
            for table_name, table_obj in Base.metadata.tables.items():
                if not inspector.has_table(table_name):
                    logger.warning(f"Tabela {table_name} não existe. O SQLAlchemy deve criá-la no startup.")
                    continue

                # Colunas existentes no banco
                existing_columns = [c["name"] for c in inspector.get_columns(table_name)]
                
                # Verificar cada coluna definida no modelo
                for col_name, col_obj in table_obj.columns.items():
                    if col_name not in existing_columns:
                        # Caso especial: se o modelo tem 'position' mas o banco tem 'order'
                        if col_name == "position" and "order" in existing_columns:
                            logger.info(f"Renomeando coluna 'order' para 'position' na tabela {table_name}")
                            try:
                                # SQLite não suporta RENAME COLUMN em versões muito antigas, 
                                # mas suporta a partir de 3.25.0 (2018).
                                conn.execute(text(f"ALTER TABLE {table_name} RENAME COLUMN \"order\" TO position"))
                                conn.commit()
                                continue
                            except Exception as e:
                                logger.error(f"Erro ao renomear order -> position: {e}")

                        # Adicionar nova coluna
                        logger.info(f"Adicionando coluna faltante '{col_name}' na tabela '{table_name}'")
                        try:
                            # Converte o tipo SQLAlchemy em string SQL
                            col_type = str(col_obj.type.compile(engine.dialect))
                            default_clause = ""
                            if col_obj.default is not None:
                                default_val = col_obj.default.arg
                                if isinstance(default_val, (str, bool, int)):
                                    default_clause = f" DEFAULT {int(default_val) if isinstance(default_val, bool) else default_val}"

                            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}{default_clause}"))
                            conn.commit()
                        except Exception as e:
                            logger.error(f"Falha ao adicionar coluna {col_name} em {table_name}: {e}")

        logger.info("Migração concluída.")
        return True

if __name__ == "__main__":
    DatabaseMigrator.migrate()
