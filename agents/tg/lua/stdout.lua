
local JSON = (loadfile "lua/JSON.lua")()

function ok_cb(extra, success, result)
end

function on_msg_receive (msg)
  print(JSON:encode(msg))
end

function on_our_id (id)
end

function cron()
end

function on_binlog_replay_end ()
end

function on_user_update (user, what)
end

function on_chat_update (chat, what)
end

function on_secret_chat_update (schat, what)
end

function on_get_difference_end ()
end

