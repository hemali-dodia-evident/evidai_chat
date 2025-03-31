from django.db import models

# Create your models here.
class ChatSession(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.CharField(max_length=255, default='default_token')
    title = models.CharField(max_length=255, default='Assisting New Query')
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    show = models.BooleanField(default=True)
    class Meta:
        db_table = 'chat_sessions'
        managed = False

class Conversation(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.CharField(max_length=255, default='default_token')
    chat_session_id = models.BigIntegerField()
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_asset = models.TextField(null=True)
    last_ques_cat = models.TextField(null=True)
    class Meta:
        db_table = 'conversations'
        managed = False 

class BasicPrompts(models.Model):
    id = models.BigAutoField(primary_key=True)
    prompt_category = models.TextField()
    prompt = models.TextField()
    asset_name = models.TextField(null=True)
    asset_sub_cat = models.TextField(null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    
    # def __str__(self):
    #     return self.prompt
    
    class Meta:
        db_table = 'evidai_prompts'
        managed = False

class UserChatLogin(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.IntegerField()
    token = models.TextField()

    class Meta:
        db_table = "user_chat_evidai"
        managed = False

class Asset_Key_Highlights(models.Model):
    id = models.AutoField(primary_key=True)
    asset_id = models.IntegerField(null=True, blank=True)
    text = models.CharField(max_length=100, null=True, blank=True)
    sort_order = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'asset_key_highlights'
        managed = False

class Asset(models.Model):
    id = models.AutoField(primary_key=True)
    asset_vertical_id = models.IntegerField()
    user_id = models.IntegerField()
    company_id = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    cover_image = models.CharField(max_length=255)
    currency = models.CharField(max_length=255)
    traded_volume = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    status = models.CharField(max_length=255, default="draft")
    pitch = models.TextField(blank=True, null=True)
    asset_code = models.CharField(max_length=255)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    asa_id = models.IntegerField(blank=True, null=True)
    logo_image = models.TextField(blank=True, null=True)
    short_url = models.CharField(max_length=255, blank=True, null=True)
    poll_status = models.CharField(max_length=255, default="IN_TRADING")
    retirement_eligible = models.BooleanField(default=False)
    investment_mode = models.CharField(max_length=255, default="Trading")
    invite_link = models.CharField(max_length=255, blank=True, null=True)
    asset_share_class_id = models.IntegerField(blank=True, null=True)
    investment_structure_id = models.IntegerField(blank=True, null=True)
    plan_id = models.IntegerField(blank=True, null=True)
    thumbnail_cover_image = models.CharField(max_length=255, blank=True, null=True)
    small_cover_image = models.CharField(max_length=255, blank=True, null=True)
    medium_cover_image = models.CharField(max_length=255, blank=True, null=True)
    large_cover_image = models.CharField(max_length=255, null=True, blank=True)
    asset_share_class = models.CharField(max_length=255, null=True, blank=True)
    old_structure = models.BooleanField(default=False)
    basic_details_editable = models.BooleanField(default=True)
    app_id = models.CharField(max_length=255, null=True, blank=True)
    wallet_address = models.CharField(max_length=255, null=True, blank=True)
    is_nda_created = models.BooleanField(default=False)
    qr_generated = models.BooleanField(default=False)
    is_water_testing = models.BooleanField(default=False)
    wallet_balance = models.FloatField(default=0.0)
    net_asset_value = models.FloatField(default=0.0)
    total_valuation = models.FloatField(default=0.0)
    status_tag = models.CharField(max_length=255, default="New")
    published_at = models.DateTimeField(null=True, blank=True)
    visibility = models.TextField(default="PUBLIC")
    private_short_url = models.CharField(max_length=255, null=True, blank=True)
    sort_order = models.IntegerField(default=0)
    trade_fees = models.FloatField(default=0.0)
    multisig_address = models.CharField(max_length=255, null=True, blank=True)
    structure_model = models.TextField(null=True, blank=True)
    did = models.CharField(max_length=255, null=True, blank=True)
    nft_image_url = models.CharField(max_length=255, null=True, blank=True)
    structuring = models.CharField(max_length=255, null=True, blank=True)
    rate_of_return = models.FloatField(default=0.0)
    exit_strategy = models.CharField(max_length=255, null=True, blank=True)
    class Meta:
        db_table = 'assets'
        managed = False

class CommitmentDetails(models.Model):
    id = models.AutoField(primary_key=True)  # Primary key with auto-increment
    asset_id = models.IntegerField(null=True, blank=True)  # Optional integer field
    title = models.CharField(max_length=255, null=True, blank=True)  # Optional string field
    status = models.CharField(max_length=255, null=True, blank=True)  # Optional string field
    minimum_target = models.FloatField(default=0.0)  # Default value for real type
    target_not_achieved = models.IntegerField(default=0)  # Default value for integer
    target_amount = models.FloatField(default=0.0)  # Default value for real type
    minimum_amount = models.FloatField(default=0.0)  # Default value for real type
    raised_amount = models.FloatField(default=0.0)  # Default value for real type
    no_of_investors = models.IntegerField(default=0)  # Default value for integer
    start_at = models.DateTimeField(null=True, blank=True)  # Optional datetime
    end_at = models.DateTimeField(null=True, blank=True)  # Optional datetime
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set on creation
    updated_at = models.DateTimeField()
    attempt = models.CharField(max_length=255)
    maximum_amount = models.IntegerField(default=0)
    new_digital_units_issued = models.IntegerField(default=0)
    use_of_proceeds = models.CharField(max_length=250, null=True, blank=True)
    is_private = models.BooleanField(default=False)
    cash_going_to_anchor = models.FloatField(default=0.0)
    cash_going_to_structure = models.FloatField(default=0.0)
    new_funds_issued_anchor = models.FloatField(default=0.0)
    funds_moved_escrow = models.FloatField(default=0.0)
    new_digital_units_from_reserve = models.FloatField(default=0.0)
    initial_raised_amount = models.FloatField(default=0.0)
    no_of_commitments = models.IntegerField(default=0)
    committer_fees = models.FloatField(default=0.0)
    introducer_fees = models.FloatField(default=0.0)
    class Meta:
        db_table='commitment_details'
        managed = False

class Document(models.Model):
    id = models.AutoField(primary_key=True)
    asset_id = models.IntegerField()
    document_category_id = models.IntegerField()
    path = models.CharField(max_length=255)
    size = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    class Meta:
        db_table='documents'
        managed = False

class Event(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    asset_id = models.IntegerField()
    title = models.CharField(max_length=255)
    content = models.TextField()
    zoom_link = models.TextField()
    created_by_evident = models.BooleanField(default=True)
    zoom_id = models.BigIntegerField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    class Meta:
        db_table='events'
        managed = False

class FAQ(models.Model):
    id = models.AutoField(primary_key=True)
    asset_id = models.IntegerField(null=True, blank=True)
    question = models.CharField(max_length=255)
    answer = models.TextField()
    is_highlighted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sort_order = models.IntegerField(default=1)

    class Meta:
        db_table = 'faqs'
        ordering = ['sort_order']
        managed = False

class PitchHighlight(models.Model):
    id = models.AutoField(primary_key=True)
    asset_id = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    sort_order = models.IntegerField(default=1)

    class Meta:
        db_table = 'pitch_highlights'
        managed = False

class Pitch(models.Model):
    id = models.AutoField(primary_key=True)
    asset_id = models.IntegerField(null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    sort_order = models.IntegerField(default=1)
    title = models.CharField(max_length=255)

    class Meta:
        db_table = 'pitches'
        managed = False  

class Trades(models.Model):
    id = models.AutoField(primary_key=True)
    unique_trade_id = models.CharField(max_length=255, unique=True)
    asset_id = models.IntegerField()
    maker_id = models.IntegerField()
    taker_id = models.IntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=20, decimal_places=2)  # Assuming price has 2 decimal places
    total_units = models.DecimalField(max_digits=20, decimal_places=2)  # Adjust decimal places if needed
    available_units = models.DecimalField(max_digits=20, decimal_places=2)
    traded_units = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    type = models.CharField(max_length=10)  # Assuming this is a short string like 'buy' or 'sell'
    offer_type = models.CharField(max_length=10)  # Assuming this is a short string like 'make'
    status = models.CharField(max_length=20)  # Assuming this is a short string like 'cancelled'
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    maker_company_id = models.IntegerField()
    taker_company_id = models.IntegerField(null=True, blank=True)
    parent_order_id = models.IntegerField(null=True, blank=True)
    number_of_clients = models.IntegerField(default=0)
    fees = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    referral_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'trades'
        managed = False

class Updates(models.Model):
    id = models.AutoField(primary_key=True)
    asset_id = models.IntegerField()
    title = models.CharField(max_length=255)  # Assuming the title will not exceed 255 characters
    description = models.TextField()  # Used for larger text like HTML content
    is_highlighted = models.BooleanField(default=False)  # Boolean field for TRUE/FALSE
    notified_at = models.DateTimeField(null=True, blank=True)  # Notification timestamp
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set on creation
    updated_at = models.DateTimeField(auto_now=True)  # Automatically updated on save
    sort_order = models.IntegerField(default=0)  # Sort order, default to 0

    class Meta:
        db_table = 'updates' 
        managed = False