package es.upm.dit.ging.predictor
import com.mongodb.spark._
import org.apache.spark.ml.classification.RandomForestClassificationModel
import org.apache.spark.ml.feature.{Bucketizer, StringIndexerModel, VectorAssembler}
// import org.apache.spark.sql.functions.{concat, from_json, lit}
import org.apache.spark.sql.functions.{concat, from_json, lit, col, struct, to_json} // AÑADIDO: col, struct, to_json
import org.apache.spark.sql.types.{DataTypes, StructType}
import org.apache.spark.sql.{DataFrame, SparkSession}

object MakePrediction {

  final val MASTER = sys.env.getOrElse("SPARK_MASTER", "local[*]")
  final val BASE_PATH = sys.env.getOrElse("BASE_PATH", "/home/tehe/Work/FBID/practica_prediccion-vuelos/practica_creativa")
  final val KAFKA_URL = sys.env.getOrElse("KAFKA_URL", "localhost:9092")
  final val MONGO_URL = sys.env.getOrElse("MONGO_URL", "mongodb://localhost:27017")

  def main(args: Array[String]): Unit = {
    println("Fligth predictor starting...")



    val spark = SparkSession
      .builder
      .appName("StructuredNetworkWordCount")
      .master(MASTER)
      .getOrCreate()
    // val spark = SparkSession
    //   .builder
    //   .appName("StructuredNetworkWordCount")
    //   .master("local[*]")
    //   .getOrCreate()
    import spark.implicits._

    // --- --- --- --- --- ---
    // --- 1. Cargar modelos ---
    // --- --- --- --- --- ---
    //Load the arrival delay bucketizer
    val base_path= BASE_PATH
    // val base_path= "/Users/admin/Downloads/practica_creativa"
    val arrivalBucketizerPath = "%s/models/arrival_bucketizer_2.0.bin".format(base_path)
    print(arrivalBucketizerPath.toString())
    val arrivalBucketizer = Bucketizer.load(arrivalBucketizerPath)
    val columns= Seq("Carrier","Origin","Dest","Route")

    //Load all the string field vectorizer pipelines into a dict
    val stringIndexerModelPath =  columns.map(n=> ("%s/models/string_indexer_model_"
      .format(base_path)+"%s.bin".format(n)).toSeq)
    val stringIndexerModel = stringIndexerModelPath.map{n => StringIndexerModel.load(n.toString)}
    val stringIndexerModels  = (columns zip stringIndexerModel).toMap

    // Load the numeric vector assembler
    val vectorAssemblerPath = "%s/models/numeric_vector_assembler.bin".format(base_path)
    val vectorAssembler = VectorAssembler.load(vectorAssemblerPath)

    // Load the classifier model
    val randomForestModelPath = "%s/models/spark_random_forest_classifier.flight_delays.5.0.bin".format(
      base_path)
    val rfc = RandomForestClassificationModel.load(randomForestModelPath)

    // --- --- --- --- --- ---
    // --- 2. Lectura de kafka  ---
    // --- --- --- --- --- ---
    //Process Prediction Requests in Streaming
    val df = spark
      .readStream
      .format("kafka")
      // .option("kafka.bootstrap.servers", "localhost:9092")
      .option("kafka.bootstrap.servers", KAFKA_URL)
      .option("subscribe", "flight-delay-ml-request")
      .load()
    df.printSchema()

    // --- --- --- --- --- ---
    // --- 3. Procesamiento  ---
    // --- --- --- --- --- ---
    val flightJsonDf = df.selectExpr("CAST(value AS STRING)")

    val flightSchema = new StructType()
      .add("Origin", DataTypes.StringType)
      .add("FlightNum", DataTypes.StringType)
      .add("DayOfWeek", DataTypes.IntegerType)
      .add("DayOfYear", DataTypes.IntegerType)
      .add("DayOfMonth", DataTypes.IntegerType)
      .add("Dest", DataTypes.StringType)
      .add("DepDelay", DataTypes.DoubleType)
      .add("Prediction", DataTypes.StringType)
      .add("Timestamp", DataTypes.TimestampType)
      .add("FlightDate", DataTypes.DateType)
      .add("Carrier", DataTypes.StringType)
      .add("UUID", DataTypes.StringType)
      .add("Distance", DataTypes.DoubleType)
      .add("Carrier_index", DataTypes.DoubleType)
      .add("Origin_index", DataTypes.DoubleType)
      .add("Dest_index", DataTypes.DoubleType)
      .add("Route_index", DataTypes.DoubleType)

    val flightNestedDf = flightJsonDf.select(from_json($"value", flightSchema).as("flight"))
    flightNestedDf.printSchema()

    // DataFrame for Vectorizing string fields with the corresponding pipeline for that column
    val flightFlattenedDf = flightNestedDf.selectExpr("flight.Origin",
      "flight.DayOfWeek","flight.DayOfYear","flight.DayOfMonth","flight.Dest",
      "flight.DepDelay","flight.Timestamp","flight.FlightDate",
      "flight.Carrier","flight.UUID","flight.Distance")
    flightFlattenedDf.printSchema()

    val predictionRequestsWithRouteMod = flightFlattenedDf.withColumn(
      "Route",
                concat(
                  flightFlattenedDf("Origin"),
                  lit('-'),
                  flightFlattenedDf("Dest")
                )
    )

    // Dataframe for Vectorizing numeric columns
    val flightFlattenedDf2 = flightNestedDf.selectExpr("flight.Origin",
      "flight.DayOfWeek","flight.DayOfYear","flight.DayOfMonth","flight.Dest",
      "flight.DepDelay","flight.Timestamp","flight.FlightDate",
      "flight.Carrier","flight.UUID","flight.Distance",
      "flight.Carrier_index","flight.Origin_index","flight.Dest_index","flight.Route_index")
    flightFlattenedDf2.printSchema()

    val predictionRequestsWithRouteMod2 = flightFlattenedDf2.withColumn(
      "Route",
      concat(
        flightFlattenedDf2("Origin"),
        lit('-'),
        flightFlattenedDf2("Dest")
      )
    )

    // Vectorize string fields with the corresponding pipeline for that column
    // Turn category fields into categoric feature vectors, then drop intermediate fields
    val predictionRequestsWithRoute = stringIndexerModel.map(n=>n.transform(predictionRequestsWithRouteMod))

    //Vectorize numeric columns: DepDelay, Distance and index columns
    val vectorizedFeatures = vectorAssembler.setHandleInvalid("keep").transform(predictionRequestsWithRouteMod2)

    // Inspect the vectors
    vectorizedFeatures.printSchema()

    // Drop the individual index columns
    val finalVectorizedFeatures = vectorizedFeatures
        .drop("Carrier_index")
        .drop("Origin_index")
        .drop("Dest_index")
        .drop("Route_index")

    // Inspect the finalized features
    finalVectorizedFeatures.printSchema()

    // Make the prediction
    val predictions = rfc.transform(finalVectorizedFeatures)
      .drop("Features_vec")

    // Drop the features vector and prediction metadata to give the original fields
    val finalPredictions = predictions.drop("indices").drop("values").drop("rawPrediction").drop("probability")



    // --- --- --- --- --- --- --- --- --- --- ---
    // --- 4. Escritura doble -> mongo y kafka  ---
    // --- --- --- --- --- --- --- --- --- --- ---
    val query = finalPredictions.writeStream
      .foreachBatch { (batchDF: DataFrame, batchId: Long) =>
        
        // Persistimos el batch en memoria porque vamos a usarlo dos veces (Mongo y Kafka)
        batchDF.persist()
        
        if (!batchDF.isEmpty) {
            println(s"Processing Batch ID: $batchId with ${batchDF.count()} records")
            
            // A) ESCRIBIR EN MONGODB (Para histórico)
            try {
                batchDF.write
                  .format("mongodb")
                  .mode("append")
                  .option("spark.mongodb.connection.uri", MONGO_URL)
                  .option("spark.mongodb.database", "agile_data_science")
                  .option("spark.mongodb.collection", "flight_delay_ml_response")
                  .save()
                println("-> Escrito en MongoDB")
            } catch {
                case e: Exception => println(s"Error escribiendo en Mongo: ${e.getMessage}")
            }

            // B) ESCRIBIR EN KAFKA (Para respuesta en tiempo real)
            // Kafka necesita una columna "key" (opcional) y una columna "value" (obligatoria, string/bytes)
            try {
                batchDF.select(
                    col("UUID").cast(DataTypes.StringType).alias("key"), // Usamos UUID como clave
                    to_json(struct("*")).alias("value")                  // Convertimos todo el objeto a JSON String
                  )
                  .write
                  .format("kafka")
                  .option("kafka.bootstrap.servers", KAFKA_URL)
                  .option("topic", "flight-delay-ml-response") // Topic de RESPUESTA
                  .save()
                println("-> Escrito en Kafka (flight-delay-ml-response)")
            } catch {
                case e: Exception => println(s"Error escribiendo en Kafka: ${e.getMessage}")
            }
        }
        
        // Liberamos memoria
        batchDF.unpersist()
        ()
      }
      .option("checkpointLocation", "/tmp/checkpoints_v2") // Importante cambiar o limpiar si cambia la lógica
      .start()

    query.awaitTermination()
    
    // // Inspect the output
    // finalPredictions.printSchema()

    // // define a streaming query
    // val dataStreamWriter = finalPredictions
    //   .writeStream
    //   .format("mongodb")
    //   .option("spark.mongodb.connection.uri", MONGO_URL)
    //   .option("spark.mongodb.database", "agile_data_science")
    //   .option("checkpointLocation", "/tmp")
    //   .option("spark.mongodb.collection", "flight_delay_ml_response")
    //   .outputMode("append")

    // // run the query
    // val query = dataStreamWriter.start()
    // // Console Output for predictions

    // val consoleOutput = finalPredictions.writeStream
    //   .outputMode("append")
    //   .format("console")
    //   .start()
    // consoleOutput.awaitTermination()
  }

}
