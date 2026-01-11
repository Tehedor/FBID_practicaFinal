#!/usr/bin/env bash

# Extract to Agile_Data_Code_2/data/on_time_performance.parquet, wherever we are executed from
cd ./data/
curl -Lko ./simple_flight_delay_features.jsonl.bz2 http://s3.amazonaws.com/agile_data_science/simple_flight_delay_features.jsonl.bz2

# Get the distances between pairs of airports
curl -Lko ./origin_dest_distances.jsonl http://s3.amazonaws.com/agile_data_science/origin_dest_distances.jsonl
