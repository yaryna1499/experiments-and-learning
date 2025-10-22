import asyncio
from pathlib import Path

from aiobotocore.config import AioConfig
from aiobotocore.session import get_session
from botocore import UNSIGNED


class S3Downloader:
    """Simple S3 downloader for financial data index files."""
    
    def __init__(self, bucket_name: str = "as-data-index"):
        self.bucket_name = bucket_name
        self.session = get_session()
    
    async def download_index_file(self, dataset_folder: str, tradedate: str, local_path: str) -> bool:
        """Download index file from S3."""
        try:
            # Generate bucket name with year
            year = tradedate[:4]
            bucket_name = dataset_folder.replace("yyyy", year)
            
            # Try .csv.gz first, then .csv
            for ext in [".csv.gz", ".csv"]:
                s3_key = f"{bucket_name}/{tradedate}{ext}"
                
                try:
                    await self._download_from_s3(s3_key, local_path)
                    print(f"✅ Downloaded: {dataset_folder} -> {local_path}")
                    return True
                except Exception as e:
                    if ext == ".csv":  # Last attempt failed
                        raise e
                    continue
                    
        except Exception as e:
            print(f"⚠️  Failed {dataset_folder}: {str(e)[:100]}...")
            return False
    
    async def _download_from_s3(self, s3_key: str, local_path: str) -> None:
        """Download file from S3 using anonymous access."""
        config = AioConfig(signature_version=UNSIGNED)
        
        async with self.session.create_client("s3", config=config) as client:
            response = await client.get_object(Bucket=self.bucket_name, Key=s3_key)
            
            # Create directory if needed
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_path, 'wb') as f:
                async for chunk in response['Body']:
                    f.write(chunk)


async def download_all_files(bucket_mapping: dict[str, str], tradedate: str) -> None:
    """Download all index files for a given trade date."""
    downloader = S3Downloader()
    
    successful = 0
    total = len(bucket_mapping)
    
    for dataset_folder, bucket_text_id in bucket_mapping.items():
        local_path = f"./downloads/{bucket_text_id}.csv.gz"
        
        if await downloader.download_index_file(dataset_folder, tradedate, local_path):
            successful += 1
    
    print(f"\n🎉 Downloaded {successful}/{total} files!")


async def main(bucket_mapping: dict[str, str], tradedate: str) -> None:
    """Main function to download S3 index files."""
    await download_all_files(bucket_mapping, tradedate)

# Configuration constants
TRADEDATE = "20220103"

# Dataset folder to bucket text ID mapping
DATASET_MAPPING: dict[str, str] = {
    "us-equity-1min-retail-indicators-yyyy": "eq_ret_indic_1min",
    "us-equity-direct-feed-yyyy": "eq_full_depth",
    "us-equity-bbg-1min-trades-adjusted-yyyy": "eq_trades_1min_ind_std_adj",
    "us-equity-trades-yyyy": "eq_trades",
    "us-equity-1min-trades-adjusted-yyyy": "eq_trades_1min_adj",
    "us-equity-1min-trades-yyyy": "eq_trades_1min",
    "us-equity-1min-trades-nofinra-yyyy": "eq_trades_1min_nofinra",
    "us-equity-1sec-trades-nofinra-yyyy": "eq_trades_1sec_nofinra",
    "us-equity-taq-yyyy": "eq_taq",
    "us-equity-1min-taq-ext-yyyy": "eq_taq_1min_ext",
    "us-equity-1sec-taq-ext-yyyy": "eq_taq_1sec_ext",
    "us-equity-1sec-taq-ext-nofinra-yyyy": "eq_taq_1sec_ext_no_finra",
    "us-equity-1min-taq-yyyy": "eq_taq_1min",
    "us-equity-1min-taq-nofinra-yyyy": "eq_taq_1min_nofinra",
    "us-futures-options-trades-yyyy": "fut_opt_trades",
    "us-futures-options-1min-trades-yyyy": "fut_opt_trades_1min",
    "us-futures-options-taq-yyyy": "fut_opt_taq",
    "us-futures-options-1min-taq-yyyy": "fut_opt_taq_1min",
    "us-futures-multiple-depth-yyyy": "fut_mult_depth",
    "us-futures-trades-yyyy": "fut_trades",
    "us-futures-1min-trades-yyyy": "fut_trades_1min",
    "us-futures-1sec-trades-yyyy": "fut_trades_1sec",
    "us-futures-taq-yyyy": "fut_taq",
    "us-futures-taq-v2-yyyy": "fut_taq_v2",
    "us-futures-1min-taq-yyyy": "fut_taq_1min",
    "us-options-1min-ctaq-yyyy": "opt_ctaq_1min",
    "us-options-gth-trades-yyyy": "opt_trades_gth",
    "us-options-trades-yyyy": "opt_trades",
    "us-options-1min-trades-yyyy": "opt_trades_1min",
    "us-options-tanq-yyyy": "opt_tanq",
    "us-options-tanq-fpc-yyyy": "opt_tanq_fpc",
    "us-options-gth-taq-yyyy": "opt_taq_gth",
    "us-options-1min-taq-yyyy": "opt_taq_1min",
    "us-options-ttob-v2-yyyy": "opt_ttob_v2",
    "us-futures-spreads-multiple-depth-yyyy": "fut_spr_mult_depth",
    "us-futures-1min-trades-v3-yyyy": "fut_trades_1min_v3",
    "us-futures-spreads-trades-yyyy": "fut_spr_trades",
    "us-futures-spreads-1min-taq-v3-yyyy": "fut_spr_taq_1min_v3",
    "us-futures-spreads-taq-yyyy": "fut_spr_taq",
    "us-options-daily-taq-yyyy": "opt_taq_daily",
    "us-vix-futures-taq": "fut_vix_taq",
    "us-vix-futures-1min-taq": "fut_vix_taq_1min",
    "us-vix-futures-trades": "fut_vix_trades",
    "us-vix-futures-1min-trades": "fut_vix_trades_1min",
    "us-options-taq-yyyy": "opt_taq",
    "us-options-taq-fpc-yyyy": "opt_taq_fpc",
    "us-options-ttob-yyyy": "opt_ttob",
}


if __name__ == "__main__":
    try:
        asyncio.run(main(DATASET_MAPPING, TRADEDATE))
    except KeyboardInterrupt:
        print("Script interrupted by user")
    except Exception as e:
        print(f"Script execution failed: {e}")
        exit(1)