import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import numpy as np

def convert_tsv_to_parquet_chunked(tsv_file_path, parquet_file_path, chunk_size=100000):
    parquet_writer = None
    schema = None

    for chunk in pd.read_csv(tsv_file_path, sep='\t', chunksize=chunk_size, low_memory=False):
        # Замена '\\N' на NaN
        chunk.replace('\\N', np.nan, inplace=True)

        # Фильтрация по столбцу 'region' и выбор столбцов 'titleId', 'title' и 'region'
        filtered_chunk = chunk[chunk['region'] == 'RU'][['titleId', 'title', 'region']]

        # Если после фильтрации чанк пустой, пропустить его
        if filtered_chunk.empty:
            continue

        table = pa.Table.from_pandas(filtered_chunk)

        if schema is None:
            schema = table.schema

        if parquet_writer is None:
            parquet_writer = pq.ParquetWriter(parquet_file_path, schema=schema)

        parquet_writer.write_table(table=table)

    if parquet_writer:
        parquet_writer.close()

tsv_file_path = 'path'
parquet_file_path = 'path'