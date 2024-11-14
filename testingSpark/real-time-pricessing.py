# Import required packages
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    BooleanType,
    TimestampType,
    ArrayType,
)
from pyspark.sql.functions import (
    from_json,
    col,
    current_timestamp,
    size,
    avg,
    count,
    sum,
    when,
    datediff,
    current_date,
    year,
    month,
    to_date,
    explode,
    desc,
    max as max_,  # Import max as max_ to avoid conflict with Python's max
    min as min_,  # Import min as min_ to avoid conflict with Python's min
)
from pyspark.sql.window import Window
import time
import logging
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Optional: Set logging levels for other loggers
logging.getLogger("org").setLevel(logging.WARN)
logging.getLogger("akka").setLevel(logging.WARN)

# Initialize Spark Session
# spark = SparkSession.builder.appName("EmployeeAnalytics")\
#         .config(
#             "spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0"
#         )\
#         .config("spark.streaming.stopGracefullyOnShutdown", "true")\
#         .config("spark.sql.streaming.schemaInference", "true")\
#         .config("spark.sql.shuffle.partitions", "2")\
#         .config("spark.default.parallelism", "2")\
#         .config("spark.streaming.kafka.consumer.cache.enabled", "false")\
#         .config("spark.executor.memory", "1g")\
#         .config("spark.driver.memory", "1g")\
#         .master("local[2]")\
#         .getOrCreate()
# Initialize Spark Session with better memory configuration
        # 

spark = (
    SparkSession.builder.appName("EmployeeAnalytics")
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0")
    .config("spark.streaming.stopGracefullyOnShutdown", "true")
    .config("spark.sql.streaming.schemaInference", "true")
    .config("spark.sql.shuffle.partitions", "8")
    .config("spark.default.parallelism", "8")
    .config("spark.streaming.kafka.consumer.cache.enabled", "false")
    .config("spark.executor.memory", "20g")
    .config("spark.driver.memory", "20g")
    .config("spark.memory.offHeap.enabled", "true")
    .config("spark.memory.offHeap.size", "20g")
    .config("spark.sql.shuffle.partitions", "8")
    .config("spark.executor.cores", "2")
    .config("spark.driver.maxResultSize", "10g")
    .config("spark.memory.fraction", "0.8")
    .config("spark.memory.storageFraction", "0.3")
    .master("local[4]")
    .getOrCreate()
)       
# Set Spark log level - choose one of these levels: ERROR, WARN, INFO, DEBUG
spark.sparkContext.setLogLevel("ERROR")

# Optional: Also set root logger to reduce other noise
logging.getLogger("org").setLevel(logging.WARN)
logging.getLogger("akka").setLevel(logging.WARN)
# Log Spark application ID
logger.info(f"Spark Application ID: {spark.sparkContext.applicationId}")

# Define schema for the incoming JSON data
schema = StructType(
    [
        StructField(
            "metadata",
            StructType(
                [
                    StructField("record_id", StringType()),
                    StructField("timestamp", StringType()),
                    StructField("version", StringType()),
                    StructField("data_center", StringType()),
                ]
            ),
        ),
        StructField(
            "employee",
            StructType(
                [
                    StructField("id", StringType()),
                    StructField("name", StringType()),
                    StructField("email", StringType()),
                    StructField("phone", StringType()),
                    StructField("department", StringType()),
                    StructField("position", StringType()),
                    StructField("experience_level", StringType()),
                    StructField("employment_status", StringType()),
                ]
            ),
        ),
        StructField(
            "compensation",
            StructType(
                [
                    StructField("salary", IntegerType()),
                    StructField("bonus_eligible", BooleanType()),
                    StructField("stock_options", IntegerType()),
                ]
            ),
        ),
        StructField(
            "location",
            StructType(
                [
                    StructField("office", StringType()),
                    StructField("timezone", StringType()),
                    StructField("country", StringType()),
                    StructField("remote_work_eligible", BooleanType()),
                ]
            ),
        ),
        StructField(
            "dates",
            StructType(
                [
                    StructField("join_date", StringType()),
                    StructField("last_promotion_date", StringType()),
                    StructField("last_review_date", StringType()),
                ]
            ),
        ),
        StructField(
            "performance",
            StructType(
                [
                    StructField("last_rating", StringType()),
                    StructField("rating_date", StringType()),
                    StructField("projects_completed", IntegerType()),
                ]
            ),
        ),
    ]
)

# Start time for performance tracking


# Read from Kafka
raw_df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "testing")
    .option("startingOffsets", "latest")
    .load()
)

# Monitor raw Kafka data
logger.info("=== RAW KAFKA STREAM SCHEMA ===")
raw_df.printSchema()

# Define schema for the batch wrapper
batch_schema = StructType(
    [
        StructField("batch_id", StringType()),
        StructField("batch_timestamp", StringType()),
        StructField("record_count", IntegerType()),
        StructField("records", ArrayType(schema)),  # Using the existing record schema
    ]
)
def process_batch(df, epoch_id):
    start_time = time.time()
    logger.info(f"\n\n\nProcessing batch {epoch_id}")

    if df.count() == 0:
        logger.warning("No messages received in this batch")
        return

    # Parse the JSON data with the new batch schema
    parsed_df = (
        df.selectExpr(
            "CAST(value AS STRING) as json_data", "timestamp as kafka_timestamp"
        )
        .select(
            from_json("json_data", batch_schema).alias("batch_data"), "kafka_timestamp"
        )
        .select(
            "batch_data.batch_id",
            "batch_data.batch_timestamp",
            "batch_data.record_count",
            "batch_data.records",
            "kafka_timestamp",
        )
    )

    # Explode the records array to get individual records
    parsed_df = parsed_df.select(
        "batch_id",
        "batch_timestamp",
        explode("records").alias("record"),
        "kafka_timestamp",
    ).select("batch_id", "batch_timestamp", "record.*", "kafka_timestamp")

    # Log batch info
    record_count = parsed_df.count()
    logger.info(f"\nProcessing {record_count} records in this batch")

    # Create multiple analysis dataframes with windowed aggregations
    window_spec = Window.partitionBy("processing_time").orderBy("kafka_timestamp")


    # 1. Salary Analysis by Department and Position - with running averages
    salary_analysis = (
        parsed_df.groupBy(col("employee.department"), col("employee.position"))
        .agg(
            avg("compensation.salary").alias("avg_salary"),
            count("*").alias("employee_count"),
            max_("compensation.salary").alias("max_salary"),
            min_("compensation.salary").alias("min_salary")
        )
        .orderBy(desc("avg_salary"))
    )

    # 2. Remote Work Analysis with geographical distribution
    remote_work_analysis = (
        parsed_df.groupBy(col("location.country"), col("location.office"))
        .agg(
            count("*").alias("total_employees"),
            sum(
                when(col("location.remote_work_eligible") == True, 1).otherwise(0)
            ).alias("remote_eligible_count"),
            (
                sum(when(col("location.remote_work_eligible") == True, 1).otherwise(0))
                / count("*")
                * 100
            ).alias("remote_eligible_percentage"),
        )
        .orderBy(desc("total_employees"))
    )

    # 3. Performance Analysis with experience level correlation
    performance_analysis = (
        parsed_df.groupBy(
            col("employee.department"),
            col("employee.experience_level"),
            col("performance.last_rating"),
        )
        .agg(
            count("*").alias("employee_count"),
            avg("performance.projects_completed").alias("avg_projects_completed"),
            avg("compensation.salary").alias("avg_salary"),
        )
        .orderBy("department", "experience_level")
    )

    # 4. Comprehensive Compensation Analysis
    compensation_analysis = parsed_df.groupBy(
        col("employee.department"), col("employee.experience_level")
    ).agg(
        avg("compensation.salary").alias("avg_salary"),
        sum(when(col("compensation.bonus_eligible") == True, 1).otherwise(0)).alias(
            "bonus_eligible_count"
        ),
        avg("compensation.stock_options").alias("avg_stock_options"),
        min_("compensation.salary").alias("min_salary"),
        max_("compensation.salary").alias("max_salary"),
    )

    # 5. Enhanced Tenure Analysis
    tenure_analysis = parsed_df.select(
        col("employee.department"),
        col("employee.position"),
        col("employee.experience_level"),
        datediff(current_date(), to_date(col("dates.join_date"))).alias("tenure_days"),
        datediff(current_date(), to_date(col("dates.last_promotion_date"))).alias(
            "days_since_last_promotion"
        ),
        col("performance.last_rating"),
        col("compensation.salary"),
    ).orderBy(desc("tenure_days"))

    # Print insights with better formatting
    logger.info("\n📊 BATCH PROCESSING INSIGHTS SUMMARY")
    logger.info("=" * 80)

    # Print all analyses with proper headers and formatting
    analyses = [
        ("1. Salary Analysis by Department and Position", salary_analysis),
        ("2. Remote Work Distribution", remote_work_analysis),
        ("3. Performance Metrics", performance_analysis),
        ("4. Compensation Structure", compensation_analysis),
        ("5. Tenure and Career Progress", tenure_analysis),
    ]

    # for title, analysis_df in analyses:
    #     logger.info(f"\n{title}")
    #     # logger.info("-" * 40)
    #     analysis_df.show(truncate=False)

    # Calculate and show batch summary statistics
    logger.info("\n📈 Batch Summary Metrics")
    # logger.info("-" * 40)

    summary_stats = {
        "Total Records Processed": record_count,
        "Average Salary": parsed_df.select(avg("compensation.salary")).first()[0],
        "Remote Work Percentage": (
            parsed_df.filter(col("location.remote_work_eligible") == True).count()
            / record_count
            * 100
        ),
        "Bonus Eligible Percentage": (
            parsed_df.filter(col("compensation.bonus_eligible") == True).count()
            / record_count
            * 100
        ),
        "Processing Time (seconds)": time.time() - start_time,
    }

    for metric, value in summary_stats.items():
        if isinstance(value, float):
            logger.info(f"{metric}: {value:,.2f}")
        else:
            logger.info(f"{metric}: {value:,}")

    logger.info("=" * 80 + "\n")
    
query = raw_df.writeStream.foreachBatch(process_batch).start()

# Wait for the streaming to run
query.awaitTermination()
