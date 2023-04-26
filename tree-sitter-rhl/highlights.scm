(identifier) @variable
(variable_declaration [":" "="] @operator)
(variable_assignment ["="] @operator)
(binary_expression operator: _ @operator)

(function_declaration (identifier) @function)
(parameter (identifier) @parameter)

(call function: (identifier) @function.call)

(basic_type) @type
(func_type ["func"] @type)
(list_type ["list"] @type)

(string) @string
(boolean) @boolean
(integer) @number
(rational) @float
(none) @constant.builtin

["fun"] @keyword.function

["return"] @keyword.return

["if" "else"] @conditional

["while"] @repeat


;; [
;;   "->"
;;   ":="
;; ] @operator
