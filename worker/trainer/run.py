import sys
import logging
import os
from recommendationEngine.ALS_recommendation import ALSRecommender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test():

    logger.info(os.getenv("REMOTE"))
    engine = ALSRecommender()
    av = engine.get_interaction_data()
    logger.info(av.head)
    logger.info(os.getenv("REMOTE"))

def retrain_model():


    engine = ALSRecommender()
    logger.info("Starting Retraining")
    engine.create()
    logger.info("Done retraining")


if __name__ == "__main__":

    #test()
    retrain_model()
