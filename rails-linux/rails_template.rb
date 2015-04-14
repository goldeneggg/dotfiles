# -----
# my rails Gemfile template
#    http://tech.kayac.com/archive/adventcalendar2014_12.html
#    http://guides.rubyonrails.org/rails_application_templates.html
# -----

#- "gem"
#-- Adds gem entry

gem 'kaminari', '~> 0.16'
gem 'kaminari-bootstrap', '~> 3.0'
gem 'active_model_serializers', '~> 0.9'
gem 'annotate', git: 'git://github.com/ctran/annotate_models.git'


#- "gem_group"
#-- Adds gem inside a group(specified by envrinment symbols)

gem_group :development do
  gem 'rack-mini-profiler'
  gem 'http-dump'
  gem 'unicorn'
end

gem_group :test do
  gem 'database_rewinder'
  gem 'selenium-webdriver'
  gem 'capybara'
end

gem_group :development, :test do
  gem 'rspec-rails', '~> 3.2'
  gem 'rspec-given', '~> 3.7'
  gem 'factory_girl_rails', '~> 4.5'
  #gem 'shoulda-matchers', '~> 2.8'

  gem 'pry', '~> 0.10'
  gem 'pry-doc' ,'~> 0.6'
  gem 'pry-rails', '~> 0.3'
  gem 'pry-remote', '~> 0.1'
  gem 'pry-byebug', '~> 3.1'
  gem 'pry-stack_explorer', '~> 0.4'
  gem 'pry-macro', '~> 1.0'
  gem 'pry-theme'
  gem 'hirb'
  gem 'hirb-unicode'
end


#- "add_source"
#-- Adds the given source to the generated application's Gemfile

# add_source https://raw.githubusercontent.com/goldenegggg/hoge/master/rails_template_source.rb


#- "environment", "application"
#-- Adds a line inside the Application class for config/application.rb.
#-- If options[:env] is specified, the line is appended to the corresponding file in config/environments.

# environment 'config.action_mailer.default_url_options = {host: "http://yourwebsite.example.com"}', env: 'production'


#- "vendor" "lib" "file" "initializer"
#-- Adds an
#---  vendor to the generated application's config/vendor directory.
#---  lib to the generated application's config/lib directory.
#---  initializer to the generated application's config/initializers directory.
#---  file  which accepts a relative path from Rails.root and creates all the directories/files needed

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

# rake("rails:freeze:gems") if yes?("Freeze rails gems?")

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


rake("db:create") if yes?("Run db:create task? (y/n) > ")
rake("db:migrate") if yes?("Run db:migrate task? (y/n) > ")
