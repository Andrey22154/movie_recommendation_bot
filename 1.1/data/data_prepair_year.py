import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import numpy as np

def convert_tsv_to_parquet_chunked_year(tsv_file_path, parquet_file_path, chunk_size=100000):
    parquet_writer = None
    schema = None

    for chunk in pd.read_csv(tsv_file_path, sep='\t', chunksize=chunk_size, low_memory=False):
        # Замена нечисловых значений на NaN и преобразование столбца 'isAdult' в float
        chunk['isAdult'].replace('\\N', np.nan, inplace=True)
        chunk['isAdult'] = chunk['isAdult'].astype('float64')

        # Выбор нужных столбцов
        selected_chunk = chunk[['tconst', 'isAdult', 'startYear', 'genres']]

        table = pa.Table.from_pandas(selected_chunk)

        if schema is None:
            schema = table.schema

        if parquet_writer is None:
            parquet_writer = pq.ParquetWriter(parquet_file_path, schema=schema)

        parquet_writer.write_table(table=table)

    if parquet_writer:
        parquet_writer.close()
