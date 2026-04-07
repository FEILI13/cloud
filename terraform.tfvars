region                      = "us-east-1"
instance_type               = "t3.micro"
ssh_key_name                = "cloud"
ssh_cidr_blocks             = ["0.0.0.0/0"]
excluded_availability_zones = ["us-east-1e"]

asg_min_size         = 2
asg_max_size         = 4
asg_desired_capacity = 2

db_name           = "ageoverflow"
db_username       = "ageoverflow"
db_password       = "Xiaoxiao020805!"
db_instance_class = "db.t3.micro"

repo_url    = "https://github.com/FEILI13/cloud.git"
repo_subdir = "cloud_app"
