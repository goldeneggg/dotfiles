# -----
# my rails Gemfile template
#    http://tech.kayac.com/archive/adventcalendar2014_12.html
#    http://guides.rubyonrails.org/rails_application_templates.html
#
# example of 'rails new' command as follows
#  rails new APPNAME -d mysql -T --skip-bundle -m ~/rails5_template.rb
# -----

#- "gem"
#-- Adds gem entry

# an HTML, XML, SAX, and Reader parser
gem 'nokogiri', '~> 1.6.6'

# a Scope & Engine based, clean, powerful, agnostic, customizable and sophisticated paginator for Rails 3+
gem 'kaminari', '~> 0.16.3'
gem 'kaminari-bootstrap', '~> 3.0.1'

# adds an object-oriented layer of presentation logic to your Rails apps
#gem 'draper', '~> 2.1.0'

# Upload files in your Ruby applications, map them to a range of ORMs, store them on different backends.
gem 'carrierwave', '~> 0.10.0'

# Annotates Rails/ActiveRecord Models, routes, fixtures, and others based on the database schema
#gem 'annotate', git: 'git://github.com/ctran/annotate_models.git'
gem 'annotate', '~> 2.6.8'

# Making it easy to serialize models for client-side use
gem 'active_model_serializers', '~> 0.9.3'

# Switching database connection between readonly one and writable one
#gem 'switch_point', '~> 0.6.0'

# is an attempt to once and for all solve the problem of inserting and maintaining seed data in a database
gem 'seed-fu', '~> 2.3.5'

# HTTP/REST API client librar
gem 'faraday', '~> 0.9.1'

# An email validator for Rails 3+.
gem 'email_validator', '~> 1.6.0'

#- "gem_group"
#-- Adds gem inside a group(specified by envrinment symbols)

gem_group :development do
  # help to kill N+1 queries and unused eager loading
  gem 'bullet', '~> 4.14.4'

  # Provides a better error page for Rails and other Rack apps
  gem 'better_errors', '~> 2.1.1'

  # is a command line tool to easily handle events on file system modifications
  gem 'guard', '~> 2.12.5'

  # Dump http request use WebMock
  gem 'http-dump', '~> 0.1.0'

  # Profiling toolkit for Rack applications with Rails integration
  gem 'rack-mini-profiler', '~> 0.9.3'

  # is an HTTP server for Rack applications designed to only serve fast clients
  # on low-latency, high-bandwidth connections and take advantage of features in Unix/Unix-like kernels
  gem 'unicorn', '~> 4.8.3'

  # This gem logs where ActiveRecord actually loads record
  gem 'activerecord-cause', '~> 0.3.0'
end

gem_group :test do
  # Making tests easy on the fingers and eyes
  gem 'shoulda-matchers', '~> 2.8.0'

  # allows stubbing HTTP requests and setting expectations on HTTP requests
  gem 'webmock', '~> 1.21.0'

  # Strategies for cleaning databases. Can be used to ensure a clean state for testing.
  gem 'database_cleaner', '~> 1.5.1'

  # WebDriver is a tool for writing automated tests of websites
  gem 'selenium-webdriver', '~> 2.45.0'

  # is an integration testing tool for rack based web applications
  gem 'capybara', '~> 2.4.4'

  # provides a simple API to record and replay your test suite's HTTP interactions
  gem 'vcr', '~> 2.9.3'
end

gem_group :development, :test do
  gem 'rspec-rails', '~> 3.2.0'
  gem 'factory_girl_rails', '~> 4.5.0'
  #gem 'rspec-given', '~> 3.7.0'

  # a port of Data::Faker from Perl, is used to easily generate fake data: names, addresses, phone numbers, etc
  gem 'faker', '~> 1.4.3'

  # A gem providing "time travel" and "time freezing" capabilities, making it dead simple to test time-dependent code
  gem 'timecop', '~> 0.7.3'

  # Code coverage for Ruby 1.9+ with a powerful configuration library and automatic merging of coverage across test suites
  gem 'simplecov', require: false

  # for debug
  gem 'pry'
  gem 'pry-doc'
  gem 'pry-rails'
  gem 'pry-remote'
  gem 'pry-byebug'
  gem 'pry-stack_explorer'
  gem 'pry-macro'
  gem 'pry-theme'
  gem 'hirb'
  gem 'hirb-unicode'

  # a documentation generation tool for the Ruby programming language
  gem 'yard'
end


#- "add_source"
#-- Adds the given source to the generated application's Gemfile

#add_source https://raw.githubusercontent.com/goldenegggg/hoge/master/rails_template_source.rb

run 'bundle install --path vendor/bundle'


#- "environment", "application"
#-- Adds a line inside the Application class for config/application.rb.
#-- If options[:env] is specified, the line is appended to the corresponding file in config/environments.

#environment 'config.action_mailer.default_url_options = {host: "http://yourwebsite.example.com"}', env: 'production'

#application do
#  %q(
#    # Custom directories with classes and modules you want to be autoloadable
#    config.autoload_paths += %W(#{config.root}/extras)
#
#    # Force all environments to use the same logger level
#    config.log_level = :debug
#
#    # Use SQL instead of Active Record's schema dumper when creating the
#    # test database. This is necessary if your schema can't be completely
#    # dumped by the schema dumper, for example, if you have constraints
#    # or db-specific column types
#    config.active_record.schema_format = :sql
#  )
#end

application do
  %q(
    config.time_zone = 'Tokyo'
    config.i18n.default_locale = :ja

    config.generators do |g|
      g.template_engine :haml
    end
  )
end


#- "vendor" "lib" "file" "initializer"
#-- Adds an
#---  vendor to the generated application's config/vendor directory.
#---  lib to the generated application's config/lib directory.
#---  initializer to the generated application's config/initializers directory.
#---  file  which accepts a relative path from Rails.root and creates all the directories/files needed

initializer 'ar_innodb_row_format.rb', <<-CODE
ActiveSupport.on_load :active_record do
  module ActiveRecord::ConnectionAdapters

    class AbstractMysqlAdapter
      def create_table_with_innodb_row_format(table_name, options = {})
        table_options = options.merge(:options => 'ENGINE=InnoDB ROW_FORMAT=DYNAMIC')
        create_table_without_innodb_row_format(table_name, table_options) do |td|
          yield td if block_given?
        end
      end
      alias_method_chain :create_table, :innodb_row_format
    end

  end
end
CODE

#initializer 'backtrace_silencers.rb', <<-CODE
  # You can add backtrace silencers for libraries that you're using but
  # don't wish to see in your backtraces.
  #Rails.backtrace_cleaner.add_silencer{|line|line=~/my_noisy_library/}

  # You can also remove all the silencers if you're trying to debug a
  # problem that might stem from framework code.
  #Rails.backtrace_cleaner.remove_silencers!
#CODE

#initializer 'filter_parameter_logging.rb', <<-CODE
  # Configure sensitive parameters which will be filtered from the log file
  #Rails.application.config.filter_parameters += [:password]
#CODE

#initializer 'mime_types.rb', <<-CODE
  # Add new mime types for use in respond_to blocks:
  #Mime::Type.register "text/richtext", :rtf
  #Mime::Type.register_alias "text/html", :iphone
#CODE

#initializer 'session_store.rb', <<-CODE
  #Rails.application.config.session_store :cookie_store,
  #  key: '_example_session'

  # The session cookies are signed using the secret_key_base set in the config/secrets.yml configuration file.
#CODE

#initializer 'omniauth.rb', <<-CODE
#  Rails.application.config.middleware.use OmniAuth::Builder do
#    provider :twitter,
#      Rails.application.secrets.twitter_api_key,
#      Rails.application.secrets.twitter_api_secret
#  end
#CODE

#file 'app/components/foo.rb', <<-CODE
#  class Foo
#  end
#CODE


#- "rakefile"
#-- Creates a new rake file under lib/tasks with the supplied tasks

#rakefile("bootstrap.rake") do
#  <<-TASK
#    namespace :boot do
#      task :strap do
#        puts "i like boots!"
#      end
#    end
#  TASK
#end


#- "generate"
#-- run "rails generate"

#generate(:scaffold, "person", "name:string", "address:text", "age:number")

generate 'rspec:install'


#- "run"
#-- Executes an arbitrary command.

#run "rm README.rdoc"


#- "route"
#-- Adds a routing entry to the config/routes.rb

#route "root to: 'person#index'"


#- "inside"
#-- Enables you to run a command from the given directory

#inside('vendor') do
#  run "ln -s ~/commit-rails/rails rails"
#end


#- "ask"
#-- gives you a chance to get some feedback from the user and use it in your templates

#lib_name = ask("What do you want to call the shiny library ?")
#lib_name << ".rb" unless lib_name.index(".rb")
# 
#lib lib_name, <<-CODE
#  class Shiny
#  end
#CODE


#- "yes", "no"
#-- et you ask questions from templates and decide the flow based on the user's answer. 

#rake("rails:freeze:gems") if yes?("Freeze rails gems?")

on = {}
# omniauth
on["omniauth"] = yes?("Use omniauth for login by other service? (y/n) > ")
if on["omniauth"]
  gem 'omniauth', '~> 1.2'

  initializer_omniauth = ''

  if yes?("Use twitter login? (y/n) > ")
    gem 'omniauth-twitter', '~> 1.1'
    initializer_omniauth.concat <<-CODE
      Rails.application.config.middleware.use OmniAuth::Builder do
        provider :twitter,
          Rails.application.secrets.twitter_api_key,
          Rails.application.secrets.twitter_api_secret
      end
CODE
  end

  initializer 'omniauth.rb', initializer_omniauth
end


#- "git"
#-- Rails templates let you run any git command:

#git :init
#git add: "."
#git commit: "-a -m 'Initial commit'"


# add .gitignore
add_gitignore = <<CODE
.DS_Store
vendor/bundle
*.swp
tags
CODE
File.open('.gitignore', 'a') do |f|
  f.write add_gitignore
end


#- "after_bundle"
#-- Registers a callback to be executed after the gems are bundled and binstubs are generated.

after_bundle do
  git :init
  git add: "."
  git commit: %Q{ -m 'initial commit' }
end


#rake("db:create") if yes?("Run db:create task? (y/n) > ")
#rake("db:migrate") if yes?("Run db:migrate task? (y/n) > ")
