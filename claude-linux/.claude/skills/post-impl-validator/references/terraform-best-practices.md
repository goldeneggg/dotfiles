# Terraform ベストプラクティス

## はじめに

この指示ファイルは、AIコーディング支援ツールがTerraformのコードをレビューし、ベストプラクティスに沿った修正案を提示するためのガイドラインです。各項目には、レビューの観点、修正を推奨する理由の例、そして具体的な修正前後のコード例を含んでいます。

## 対象バージョン

- Terraform 1.14以上
- OpenTofu互換

---

## 1. コード構成 (Code Organization)

### 概要

適切なファイル構成とディレクトリ構造は、Terraformコードの可読性と保守性を大幅に向上させます。一貫した構造により、チームメンバーがコードを理解しやすくなります。

### レビュー観点

- ファイルが適切に分割されているか（main.tf, variables.tf, outputs.tf, versions.tf）。
- モジュール構造が適切か。
- 環境分離（dev/staging/prod）が適切に行われているか。
- 命名規則が一貫しているか。
- README.mdが用意されているか（特にモジュール）。
- リソース間の論理的なグループ化がされているか。

### 修正すべき理由の例

- **理由1:** 全てのリソースが1つのファイルに記述されており、可読性が低下しています。
- **理由2:** 環境ごとの設定がハードコードされており、環境の切り替えが困難です。
- **理由3:** モジュールにREADME.mdがなく、使用方法が不明確です。

### 修正例

#### 例1: ファイル構成

```hcl
# Before - 全てが1ファイル
# main.tf
variable "environment" {}
variable "region" {}

provider "aws" {
  region = var.region
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
}

output "vpc_id" {
  value = aws_vpc.main.id
}
```

```hcl
# After - 適切に分割されたファイル構成

# versions.tf
terraform {
  required_version = ">= 1.14.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# providers.tf
provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# variables.tf
variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-1"
}

# main.tf
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.environment}-vpc"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.environment}-public-subnet"
  }
}

# outputs.tf
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "ID of the public subnet"
  value       = aws_subnet.public.id
}
```

#### 例2: 環境分離

```
# 推奨ディレクトリ構成
project/
├── modules/
│   ├── networking/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   └── compute/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── README.md
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   │   ├── main.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── prod/
│       ├── main.tf
│       ├── terraform.tfvars
│       └── backend.tf
└── README.md
```

---

## 2. 変数管理 (Variable Management)

### 概要

適切な変数管理により、コードの再利用性と柔軟性が向上します。変数には適切な型、デフォルト値、バリデーションを設定することが重要です。

### レビュー観点

- 変数に適切な型指定がされているか。
- 必要に応じてデフォルト値が設定されているか。
- 変数のバリデーションが実装されているか。
- tfvarsファイルが適切に活用されているか。
- センシティブな変数に `sensitive = true` が設定されているか。
- 変数の説明（description）が記述されているか。

### 修正すべき理由の例

- **理由1:** 変数に型指定がなく、予期しない値が渡される可能性があります。
- **理由2:** パスワードなどのセンシティブな変数に `sensitive` フラグが設定されていません。
- **理由3:** 変数に説明がなく、使用目的が不明確です。

### 修正例

#### 例1: 変数の型指定とバリデーション

```hcl
# Before - 型指定なし、バリデーションなし
variable "instance_count" {}
variable "instance_type" {}
variable "allowed_ports" {}
```

```hcl
# After - 適切な型指定とバリデーション
variable "instance_count" {
  description = "Number of EC2 instances to create"
  type        = number
  default     = 1

  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 10
    error_message = "Instance count must be between 1 and 10."
  }
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"

  validation {
    condition     = can(regex("^t[23]\\.", var.instance_type))
    error_message = "Instance type must be t2 or t3 family."
  }
}

variable "allowed_ports" {
  description = "List of allowed inbound ports"
  type        = list(number)
  default     = [80, 443]

  validation {
    condition     = alltrue([for port in var.allowed_ports : port >= 1 && port <= 65535])
    error_message = "All ports must be between 1 and 65535."
  }
}
```

#### 例2: 複合型の変数

```hcl
# Before - 分離した変数
variable "db_host" {}
variable "db_port" {}
variable "db_name" {}
variable "db_user" {}
variable "db_password" {}
```

```hcl
# After - オブジェクト型で構造化
variable "database_config" {
  description = "Database connection configuration"
  type = object({
    host     = string
    port     = number
    name     = string
    username = string
    password = string
  })

  validation {
    condition     = var.database_config.port >= 1 && var.database_config.port <= 65535
    error_message = "Database port must be between 1 and 65535."
  }

  sensitive = true
}

# 使用例
locals {
  db_connection_string = "postgresql://${var.database_config.username}:${var.database_config.password}@${var.database_config.host}:${var.database_config.port}/${var.database_config.name}"
}
```

---

## 3. 状態管理 (State Management)

### 概要

Terraformの状態ファイルは、インフラストラクチャの現在の状態を追跡する重要なファイルです。適切な状態管理により、チームでの共同作業が可能になり、データの安全性が確保されます。

### レビュー観点

- リモートバックエンドが使用されているか。
- 状態ファイルが暗号化されているか。
- 状態のロック機構が設定されているか。
- 状態分離（ワークスペースまたはディレクトリ）が適切か。
- 状態ファイルへのアクセス制御が設定されているか。

### 修正すべき理由の例

- **理由1:** ローカルの状態ファイルを使用しており、チームでの共同作業ができません。
- **理由2:** 状態ファイルが暗号化されておらず、センシティブ情報が露出するリスクがあります。
- **理由3:** 状態のロック機構がなく、同時更新による破損のリスクがあります。

### 修正例

#### 例1: リモートバックエンド設定

```hcl
# Before - ローカルバックエンド（暗黙的）
# 設定なし - デフォルトでローカルファイル
```

```hcl
# After - S3バックエンド（推奨）
terraform {
  backend "s3" {
    bucket         = "my-terraform-state-bucket"
    key            = "environments/prod/terraform.tfstate"
    region         = "ap-northeast-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"

    # オプション: KMS暗号化
    kms_key_id = "alias/terraform-state-key"
  }
}
```

#### 例2: バックエンド用リソースの作成

```hcl
# バックエンド用のS3バケットとDynamoDBテーブルを作成するモジュール
# backend-setup/main.tf

resource "aws_s3_bucket" "terraform_state" {
  bucket = "${var.project_name}-terraform-state"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.terraform_state.arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "${var.project_name}-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_kms_key" "terraform_state" {
  description             = "KMS key for Terraform state encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}
```

---

## 4. セキュリティ (Security)

### 概要

セキュリティはインフラストラクチャ管理において最も重要な側面の1つです。Terraformコードでは、シークレットの適切な管理、最小権限の原則、セキュリティスキャンの活用が重要です。

### レビュー観点

- シークレットがハードコードされていないか。
- Secrets ManagerやVaultとの連携が適切か。
- IAMポリシーが最小権限の原則に従っているか。
- セキュリティスキャンツール（tfsec, Checkov）の指摘がないか。
- セキュリティグループが適切に制限されているか。
- 暗号化が有効になっているか。

### 修正すべき理由の例

- **理由1:** パスワードやAPIキーがコード内にハードコードされています。
- **理由2:** IAMポリシーに `*` が使用されており、過剰な権限が付与されています。
- **理由3:** セキュリティグループで `0.0.0.0/0` からの全ポートアクセスが許可されています。

### 修正例

#### 例1: シークレットの管理

```hcl
# Before - ハードコードされたシークレット
resource "aws_db_instance" "main" {
  identifier     = "mydb"
  engine         = "mysql"
  instance_class = "db.t3.micro"
  username       = "admin"
  password       = "SuperSecretPassword123!"  # 危険！
}
```

```hcl
# After - Secrets Managerを使用
data "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = "prod/db/credentials"
}

locals {
  db_credentials = jsondecode(data.aws_secretsmanager_secret_version.db_credentials.secret_string)
}

resource "aws_db_instance" "main" {
  identifier     = "mydb"
  engine         = "mysql"
  instance_class = "db.t3.micro"
  username       = local.db_credentials.username
  password       = local.db_credentials.password

  # シークレットローテーションの設定も検討
}

# または、ランダムパスワード生成
resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "db_password" {
  name = "prod/db/password"
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}
```

#### 例2: 最小権限のIAMポリシー

```hcl
# Before - 過剰な権限
resource "aws_iam_role_policy" "lambda_policy" {
  name = "lambda-policy"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "*"
        Resource = "*"
      }
    ]
  })
}
```

```hcl
# After - 最小権限の原則
resource "aws_iam_role_policy" "lambda_policy" {
  name = "lambda-policy"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.function_name}:*"
      },
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.data.arn}/*"
      },
      {
        Sid    = "DynamoDBAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ]
        Resource = aws_dynamodb_table.main.arn
      }
    ]
  })
}
```

#### 例3: セキュリティグループの制限

```hcl
# Before - 過度に開放されたセキュリティグループ
resource "aws_security_group" "web" {
  name = "web-sg"

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

```hcl
# After - 適切に制限されたセキュリティグループ
resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Security group for web servers"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "web-sg"
  }
}

resource "aws_security_group_rule" "web_https_ingress" {
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.web.id
  description       = "HTTPS from anywhere"
}

resource "aws_security_group_rule" "web_http_ingress" {
  type              = "ingress"
  from_port         = 80
  to_port           = 80
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.web.id
  description       = "HTTP from anywhere (redirect to HTTPS)"
}

resource "aws_security_group_rule" "web_egress" {
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.web.id
  description       = "HTTPS to anywhere"
}
```

---

## 5. プロバイダー管理 (Provider Management)

### 概要

プロバイダーのバージョン管理は、インフラストラクチャの再現性と安定性を確保するために重要です。

### レビュー観点

- プロバイダーのバージョンが固定されているか。
- `required_providers` ブロックが適切に設定されているか。
- プロバイダーエイリアスが必要な場合に適切に設定されているか。
- Terraform本体のバージョンが指定されているか。

### 修正すべき理由の例

- **理由1:** プロバイダーのバージョンが指定されておらず、更新時に予期しない変更が発生する可能性があります。
- **理由2:** 複数リージョンのリソースを管理する際に、プロバイダーエイリアスが使用されていません。
- **理由3:** Terraformのバージョン制約が緩すぎて、互換性の問題が発生する可能性があります。

### 修正例

#### 例1: プロバイダーバージョンの固定

```hcl
# Before - バージョン指定なし
provider "aws" {
  region = "ap-northeast-1"
}
```

```hcl
# After - 適切なバージョン指定
terraform {
  required_version = ">= 1.14.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = var.default_tags
  }
}
```

#### 例2: マルチリージョン対応

```hcl
# 複数リージョンでのプロバイダーエイリアス
provider "aws" {
  region = "ap-northeast-1"
  alias  = "tokyo"
}

provider "aws" {
  region = "us-east-1"
  alias  = "virginia"
}

# 東京リージョンのリソース
resource "aws_s3_bucket" "tokyo_bucket" {
  provider = aws.tokyo
  bucket   = "${var.project_name}-tokyo-bucket"
}

# バージニアリージョンのリソース（CloudFront用のACM証明書など）
resource "aws_acm_certificate" "virginia_cert" {
  provider          = aws.virginia
  domain_name       = var.domain_name
  validation_method = "DNS"
}
```

---

## 6. モジュール設計 (Module Design)

### 概要

モジュールは、Terraformコードの再利用性と保守性を向上させるための重要な仕組みです。適切に設計されたモジュールは、チーム全体で活用できます。

### レビュー観点

- モジュールの粒度が適切か。
- 入出力が明確に定義されているか。
- バージョンタグが付けられているか。
- ドキュメント（README.md）が整備されているか。
- モジュールの依存関係が最小限か。

### 修正すべき理由の例

- **理由1:** モジュールが大きすぎて、再利用が困難です。
- **理由2:** モジュールの入出力が文書化されておらず、使用方法が不明確です。
- **理由3:** モジュールのバージョンが管理されておらず、変更による影響が追跡できません。

### 修正例

#### 例1: モジュール構成

```hcl
# modules/vpc/main.tf
resource "aws_vpc" "main" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = var.enable_dns_hostnames
  enable_dns_support   = var.enable_dns_support

  tags = merge(
    var.tags,
    {
      Name = var.name
    }
  )
}

resource "aws_internet_gateway" "main" {
  count = var.create_igw ? 1 : 0

  vpc_id = aws_vpc.main.id

  tags = merge(
    var.tags,
    {
      Name = "${var.name}-igw"
    }
  )
}

resource "aws_subnet" "public" {
  count = length(var.public_subnets)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnets[count.index]
  availability_zone       = var.azs[count.index]
  map_public_ip_on_launch = true

  tags = merge(
    var.tags,
    {
      Name = "${var.name}-public-${var.azs[count.index]}"
      Type = "public"
    }
  )
}

resource "aws_subnet" "private" {
  count = length(var.private_subnets)

  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnets[count.index]
  availability_zone = var.azs[count.index]

  tags = merge(
    var.tags,
    {
      Name = "${var.name}-private-${var.azs[count.index]}"
      Type = "private"
    }
  )
}
```

```hcl
# modules/vpc/variables.tf
variable "name" {
  description = "Name prefix for all resources"
  type        = string
}

variable "cidr_block" {
  description = "CIDR block for the VPC"
  type        = string

  validation {
    condition     = can(cidrnetmask(var.cidr_block))
    error_message = "Must be a valid CIDR block."
  }
}

variable "azs" {
  description = "List of availability zones"
  type        = list(string)
}

variable "public_subnets" {
  description = "List of public subnet CIDR blocks"
  type        = list(string)
  default     = []
}

variable "private_subnets" {
  description = "List of private subnet CIDR blocks"
  type        = list(string)
  default     = []
}

variable "enable_dns_hostnames" {
  description = "Enable DNS hostnames in the VPC"
  type        = bool
  default     = true
}

variable "enable_dns_support" {
  description = "Enable DNS support in the VPC"
  type        = bool
  default     = true
}

variable "create_igw" {
  description = "Create an Internet Gateway"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
```

```hcl
# modules/vpc/outputs.tf
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "igw_id" {
  description = "ID of the Internet Gateway"
  value       = var.create_igw ? aws_internet_gateway.main[0].id : null
}
```

#### 例2: モジュールの使用

```hcl
# 環境でのモジュール使用
module "vpc" {
  source = "../../modules/vpc"
  # または外部モジュール
  # source  = "terraform-aws-modules/vpc/aws"
  # version = "5.0.0"

  name       = "${var.project_name}-${var.environment}"
  cidr_block = var.vpc_cidr

  azs             = ["ap-northeast-1a", "ap-northeast-1c", "ap-northeast-1d"]
  public_subnets  = var.public_subnet_cidrs
  private_subnets = var.private_subnet_cidrs

  create_igw = true

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}
```

---

## 7. リソース定義 (Resource Definition)

### 概要

リソースの定義は、Terraformコードの中核です。適切な命名規則、タグ付け、依存関係の管理により、インフラストラクチャの管理が容易になります。

### レビュー観点

- リソースの命名規則が一貫しているか。
- タグ付けポリシーに従っているか。
- `depends_on` が適切に使用されているか（暗黙的依存関係で十分な場合は使用しない）。
- `count` vs `for_each` の使い分けが適切か。
- ライフサイクルルールが適切に設定されているか。

### 修正すべき理由の例

- **理由1:** リソース名が一貫しておらず、管理が困難です。
- **理由2:** `count` を使用しているため、中間要素の削除時に問題が発生する可能性があります。
- **理由3:** 本番環境のリソースに `prevent_destroy` が設定されていません。

### 修正例

#### 例1: count vs for_each

```hcl
# Before - countを使用（順序依存の問題あり）
variable "subnet_cidrs" {
  default = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

resource "aws_subnet" "subnets" {
  count = length(var.subnet_cidrs)

  vpc_id     = aws_vpc.main.id
  cidr_block = var.subnet_cidrs[count.index]

  tags = {
    Name = "subnet-${count.index}"
  }
}
```

```hcl
# After - for_eachを使用（順序に依存しない）
variable "subnets" {
  default = {
    "public-1a" = {
      cidr_block        = "10.0.1.0/24"
      availability_zone = "ap-northeast-1a"
      public            = true
    }
    "public-1c" = {
      cidr_block        = "10.0.2.0/24"
      availability_zone = "ap-northeast-1c"
      public            = true
    }
    "private-1a" = {
      cidr_block        = "10.0.11.0/24"
      availability_zone = "ap-northeast-1a"
      public            = false
    }
  }
}

resource "aws_subnet" "subnets" {
  for_each = var.subnets

  vpc_id                  = aws_vpc.main.id
  cidr_block              = each.value.cidr_block
  availability_zone       = each.value.availability_zone
  map_public_ip_on_launch = each.value.public

  tags = {
    Name   = "${var.project_name}-${each.key}"
    Public = each.value.public
  }
}
```

#### 例2: ライフサイクルルール

```hcl
# 本番環境の重要リソース
resource "aws_rds_cluster" "production" {
  cluster_identifier = "${var.project_name}-prod"
  engine             = "aurora-mysql"
  engine_version     = "8.0.mysql_aurora.3.04.0"

  database_name   = var.database_name
  master_username = var.master_username
  master_password = var.master_password

  backup_retention_period = 35
  preferred_backup_window = "03:00-04:00"

  deletion_protection = true

  lifecycle {
    prevent_destroy = true

    # エンジンバージョンの更新を無視
    ignore_changes = [
      engine_version,
    ]
  }

  tags = {
    Name        = "${var.project_name}-prod-cluster"
    Environment = "production"
    Critical    = "true"
  }
}
```

---

## 8. データソース (Data Sources)

### 概要

データソースは、既存のリソースや外部情報を参照するために使用されます。適切に使用することで、柔軟で保守性の高いコードを書けます。

### レビュー観点

- 既存リソースの参照にデータソースが使用されているか。
- 動的なデータ取得が適切に行われているか。
- データソースのフィルタリングが正確か。
- ハードコードされた値がデータソースで置き換えられるか。

### 修正すべき理由の例

- **理由1:** AMI IDがハードコードされており、リージョン変更時に問題が発生します。
- **理由2:** アカウントIDがハードコードされており、他の環境で再利用できません。
- **理由3:** 既存のリソースを参照する際にデータソースが使用されていません。

### 修正例

#### 例1: 動的なAMI取得

```hcl
# Before - ハードコードされたAMI ID
resource "aws_instance" "web" {
  ami           = "ami-0123456789abcdef0"  # 特定リージョンのAMI
  instance_type = "t3.micro"
}
```

```hcl
# After - データソースで動的に取得
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = "t3.micro"

  tags = {
    Name    = "web-server"
    AMI     = data.aws_ami.amazon_linux_2023.name
    AMI_ID  = data.aws_ami.amazon_linux_2023.id
  }
}
```

#### 例2: 現在のAWSアカウント情報

```hcl
# 現在のアカウント情報を取得
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# S3バケットポリシーで使用
resource "aws_s3_bucket_policy" "logs" {
  bucket = aws_s3_bucket.logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowALBLogs"
        Effect    = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_elb_service_account.main.id}:root"
        }
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.logs.arn}/alb-logs/*"
      }
    ]
  })
}

data "aws_elb_service_account" "main" {}
```

---

## 9. 出力値 (Outputs)

### 概要

出力値は、他のモジュールやスクリプトから参照するための重要な情報を公開します。適切な出力値の定義により、モジュール間の連携が容易になります。

### レビュー観点

- 必要な値が出力されているか。
- `sensitive` 属性が適切に設定されているか。
- 出力値の説明（description）が記述されているか。
- モジュール間の値受け渡しが適切か。

### 修正すべき理由の例

- **理由1:** 重要なリソースIDが出力されておらず、他のモジュールから参照できません。
- **理由2:** センシティブな値に `sensitive` が設定されておらず、ログに出力されます。
- **理由3:** 出力値に説明がなく、用途が不明確です。

### 修正例

#### 例1: 適切な出力値定義

```hcl
# Before - 最小限の出力
output "vpc_id" {
  value = aws_vpc.main.id
}
```

```hcl
# After - 詳細な出力値
output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_arn" {
  description = "The ARN of the VPC"
  value       = aws_vpc.main.arn
}

output "vpc_cidr_block" {
  description = "The CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "List of IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "List of IDs of private subnets"
  value       = aws_subnet.private[*].id
}

output "nat_gateway_ips" {
  description = "List of public Elastic IPs created for NAT Gateway"
  value       = aws_eip.nat[*].public_ip
}

# センシティブな出力
output "database_password" {
  description = "The master password for the database"
  value       = random_password.db_password.result
  sensitive   = true
}
```

#### 例2: 複合出力

```hcl
# 複数の関連値をまとめて出力
output "vpc" {
  description = "VPC configuration object"
  value = {
    id                = aws_vpc.main.id
    arn               = aws_vpc.main.arn
    cidr_block        = aws_vpc.main.cidr_block
    public_subnet_ids = aws_subnet.public[*].id
    private_subnet_ids = aws_subnet.private[*].id
  }
}

output "endpoints" {
  description = "Service endpoints"
  value = {
    api     = "https://${aws_api_gateway_rest_api.main.id}.execute-api.${data.aws_region.current.name}.amazonaws.com"
    website = "https://${aws_cloudfront_distribution.main.domain_name}"
    rds     = aws_rds_cluster.main.endpoint
  }
}
```

---

## 10. CI/CD統合 (CI/CD Integration)

### 概要

CI/CDパイプラインとTerraformの統合により、インフラストラクチャの変更を自動化し、安全に適用できます。

### レビュー観点

- `terraform plan` が自動実行されているか。
- `terraform apply` に承認フローがあるか。
- ドリフト検出が設定されているか。
- 適切なブランチ戦略が採用されているか。
- セキュリティスキャンがパイプラインに組み込まれているか。

### 修正すべき理由の例

- **理由1:** PRレビュー時に `terraform plan` の出力が確認できません。
- **理由2:** 本番環境への適用に承認プロセスがありません。
- **理由3:** 定期的なドリフト検出が実装されていません。

### 修正例

#### 例1: GitHub Actionsワークフロー

```yaml
# .github/workflows/terraform.yml
name: Terraform

on:
  pull_request:
    branches: [main]
    paths:
      - 'terraform/**'
  push:
    branches: [main]
    paths:
      - 'terraform/**'

permissions:
  contents: read
  pull-requests: write
  id-token: write

jobs:
  terraform-plan:
    name: Terraform Plan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ap-northeast-1

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.14.0

      - name: Terraform Format Check
        run: terraform fmt -check -recursive
        working-directory: terraform

      - name: Terraform Init
        run: terraform init -backend-config=environments/${{ github.base_ref }}/backend.hcl
        working-directory: terraform

      - name: Terraform Validate
        run: terraform validate
        working-directory: terraform

      - name: Run tfsec
        uses: aquasecurity/tfsec-action@v1.0.0
        with:
          working_directory: terraform

      - name: Terraform Plan
        id: plan
        run: |
          terraform plan -var-file=environments/${{ github.base_ref }}/terraform.tfvars -out=tfplan -no-color
        working-directory: terraform
        continue-on-error: true

      - name: Comment Plan on PR
        uses: actions/github-script@v7
        if: github.event_name == 'pull_request'
        with:
          script: |
            const output = `#### Terraform Plan 📖
            \`\`\`hcl
            ${{ steps.plan.outputs.stdout }}
            \`\`\`
            `;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: output
            })

  terraform-apply:
    name: Terraform Apply
    runs-on: ubuntu-latest
    needs: terraform-plan
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ap-northeast-1

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.14.0

      - name: Terraform Init
        run: terraform init -backend-config=environments/prod/backend.hcl
        working-directory: terraform

      - name: Terraform Apply
        run: terraform apply -var-file=environments/prod/terraform.tfvars -auto-approve
        working-directory: terraform
```

---

## 11. バリデーションとフォーマット (Validation and Formatting)

### 概要

コードの品質を維持するために、フォーマットとバリデーションツールを活用することが重要です。

### レビュー観点

- `terraform fmt` でフォーマットされているか。
- `terraform validate` でエラーがないか。
- `tflint` で警告がないか。
- pre-commitフックが設定されているか。

### 修正すべき理由の例

- **理由1:** コードのフォーマットが統一されていません。
- **理由2:** `terraform validate` でエラーが発生します。
- **理由3:** tflintで検出された問題が修正されていません。

### 修正例

#### 例1: pre-commit設定

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.83.5
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_docs
        args:
          - --hook-config=--path-to-file=README.md
          - --hook-config=--add-to-existing-file=true
          - --hook-config=--create-file-if-not-exist=true
      - id: terraform_tflint
        args:
          - --args=--config=__GIT_WORKING_DIR__/.tflint.hcl
      - id: terraform_tfsec
      - id: terraform_checkov
        args:
          - --args=--quiet
          - --args=--compact
```

#### 例2: tflint設定

```hcl
# .tflint.hcl
config {
  format = "compact"
  plugin_dir = "~/.tflint.d/plugins"

  call_module_type    = "local"
  force               = false
  disabled_by_default = false
}

plugin "aws" {
  enabled = true
  version = "0.27.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

rule "terraform_deprecated_interpolation" {
  enabled = true
}

rule "terraform_deprecated_index" {
  enabled = true
}

rule "terraform_unused_declarations" {
  enabled = true
}

rule "terraform_comment_syntax" {
  enabled = true
}

rule "terraform_documented_outputs" {
  enabled = true
}

rule "terraform_documented_variables" {
  enabled = true
}

rule "terraform_typed_variables" {
  enabled = true
}

rule "terraform_naming_convention" {
  enabled = true
  format  = "snake_case"
}

rule "terraform_required_version" {
  enabled = true
}

rule "terraform_required_providers" {
  enabled = true
}

rule "terraform_standard_module_structure" {
  enabled = true
}

# AWS固有のルール
rule "aws_instance_invalid_type" {
  enabled = true
}

rule "aws_resource_missing_tags" {
  enabled = true
  tags    = ["Environment", "Project", "Owner"]
}
```

---

## まとめ

このガイドラインは、Terraformプロジェクトのコードレビューにおける主要な観点を網羅しています。以下の点を常に意識してください：

1. **コード構成**: 適切なファイル分割とディレクトリ構造
2. **変数管理**: 型指定、バリデーション、センシティブフラグ
3. **状態管理**: リモートバックエンド、暗号化、ロック機構
4. **セキュリティ**: シークレット管理、最小権限、暗号化
5. **プロバイダー管理**: バージョン固定、エイリアス
6. **モジュール設計**: 適切な粒度、ドキュメント化
7. **リソース定義**: 命名規則、タグ付け、for_each優先
8. **データソース**: 動的なデータ取得、ハードコード回避
9. **出力値**: 必要な情報の公開、センシティブ属性
10. **CI/CD統合**: 自動plan、承認フロー、ドリフト検出
11. **バリデーション**: fmt、validate、tflint、tfsec

コードレビュー時は、これらの観点を参考に、具体的な改善提案を行ってください。
