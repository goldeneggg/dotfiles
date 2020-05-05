# prompt
Pry.config.prompt = Pry::Prompt.new(
  "custom",
  "custom prompt",
  [
    proc do |obj, nest_level, _pry_|
      version = ''
      version << "[Ruby#{RUBY_VERSION}]"
      version << "[Rails#{Rails.version}]" if defined? Rails
        
      branch = ''
      branch << "\001\e[0;36m\002"
      branch << `git rev-parse --abbrev-ref HEAD`.chomp!
      branch << "\001\e[0m\002"
    
      "#{version}[#{branch}](#{obj}:#{nest_level})> "
    end
  ]
)

# theme
begin
  require 'pry-theme'
  Pry.config.theme = "pry-modern-256"
rescue LoadError
  # Missing goodies, bummer
end

# pry-byebug
if defined?(PryByebug)
  Pry.commands.alias_command 'c', 'continue'
  Pry.commands.alias_command 's', 'step'
  Pry.commands.alias_command 'n', 'next'
  Pry.commands.alias_command 'f', 'finish'
end

# awesome_print
begin
  require 'awesome_print'
  AwesomePrint.pry!
rescue LoadError
  # Missing goodies, bummer
end
