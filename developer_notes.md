# New Versions

To publish a new version of rdklib, in the RDK Maintainters account, you will need to:

1. Create a new tagged version of rdklib (`git tag X.Y.Z; git push origin X.Y.Z`)
2. Download the latest version of the SAM template from `s3://aws-sam-cli-rdklib-build-bucket-ap-southeast-1/serverlessrepo-rdklib-layer/*.template`
3. Create a new version of the SAM application using the template you downloaded.
4. Update the `rdk` repository to reference the latest Lambda Layer versions (use the `update_rdklib_versions.py` script)
