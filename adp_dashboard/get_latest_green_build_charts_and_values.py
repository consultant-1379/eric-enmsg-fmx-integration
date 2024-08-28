import logging
import os
import requests
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_latest_green_cenm_build_product_set():
    latest_green_build_ps_url = "https://ci-portal.seli.wh.rnd.internal.ericsson.com/api/cloudNative/getConfidenceLevelVersion/"
    latest_green_build_request = requests.get(url=latest_green_build_ps_url)
    latest_green_build_ps_data = latest_green_build_request.json()

    return latest_green_build_ps_data['cENM-Deploy-II-CSAR-Lite']

def fetch_product_set_content(product_set):
    current_drop = product_set[:5]
    product_set_content_url = "https://ci-portal.seli.wh.rnd.internal.ericsson.com/api/cloudnative/getCloudNativeProductSetContent/%s/%s/" % (
        current_drop, product_set)
    product_set_content_request = requests.get(url=product_set_content_url)
    product_set_content = product_set_content_request.json()

    return product_set_content

def download_integration_charts_for_cenm_product_set(product_set_content, output_file_location):
    number_of_charts = 5
    integration_charts_data_index = 1

    accepted_charts = ["eric-enm-bro-integration", "eric-enm-pre-deploy-integration", "eric-enm-infra-integration", "eric-enm-stateless-integration"]

    for i in range(number_of_charts):
        if any (product_set_content[integration_charts_data_index]['integration_charts_data'][i]["chart_name"] == chart for chart in accepted_charts):
            chart_name = product_set_content[integration_charts_data_index]['integration_charts_data'][i]["chart_name"]
            chart_version = product_set_content[integration_charts_data_index]['integration_charts_data'][i]["chart_version"]
            chart_dev_url = product_set_content[integration_charts_data_index]['integration_charts_data'][i]["chart_dev_url"]

            logger.info(f"{chart_name}: {chart_version}")
            os.system(f"wget -q -P {output_file_location} --no-check-certificate {chart_dev_url}")

def download_integration_values_file_for_cenm_product_set(product_set_content, output_file_location):
    integration_values_file_data_index = 2
    integration_production_values_file_index = 0

    single_instance_values_file = "eric-enm-single-instance-production-integration-values"
    values_file_version = product_set_content[integration_values_file_data_index]['integration_values_file_data'][integration_production_values_file_index]["values_file_version"]
    values_file_single_instance_location = "https://arm.epk.ericsson.se/artifactory/proj-enm-dev-internal-helm/eric-enm-integration-values/eric-enm-single-instance-production-integration-values-%s.yaml"
    values_file_url = values_file_single_instance_location % values_file_version

    logger.info(f"{single_instance_values_file}: {values_file_version}")
    os.system(f"wget -q -P {output_file_location} --no-check-certificate {values_file_url}")

def get_latest_cenm_product_set_and_download_integration_charts(output_file_location):
    latest_green_ps = get_latest_green_cenm_build_product_set()
    logger.info(f"Product Set: {latest_green_ps}")

    product_set_content = fetch_product_set_content(latest_green_ps)
    download_integration_charts_for_cenm_product_set(product_set_content, output_file_location)
    download_integration_values_file_for_cenm_product_set(product_set_content, output_file_location)

def main():
    output_file_location = sys.argv[1]
    get_latest_cenm_product_set_and_download_integration_charts(output_file_location)

if __name__ == "__main__":
    main()