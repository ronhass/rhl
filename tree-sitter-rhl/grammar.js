module.exports = grammar({
    name: 'rhl',

    rules: {
        source_file: $ => repeat($._statement),

        _statement: $ => choice(
            $.function_declaration,
            $.block,
            $.if,
            $.while,
            $.return,
            $.expression_statement,
        ),

        function_declaration: $ => seq(
            'fun',
            field('name', $.identifier),
            field('parameters', $._parameters),
            optional(seq(
                '->',
                field('return_type', $._type),
            )),
            field('body', $.block),
        ),

        _parameters: $ => seq(
            '(',
                sepBy(',', $.parameter, 'parameter'),
            ')',
        ),

        parameter: $ => seq(
            field('name', $.identifier),
            ':',
            field('type', $._type),
        ),

        block: $ => seq(
            '{',
                repeat($._statement),
            '}',
        ),

        if: $ => prec.right(seq(
            'if',
            field('condition', $._expression),
            field('body', $._statement),
            optional(seq(
                'else',
                field('else_body', $._statement),
            )),
        )),

        while: $ => seq(
            'while',
            field('condition', $._expression),
            field('body', $._statement),
        ),

        return: $ => seq(
            'return',
            field('expression', $._expression),
            ';',
        ),

        expression_statement: $ => seq(
            field('expression', $._expression),
            ';'
        ),

        _expression: $ => choice(
            $.call,
            $.get_item,
            $.variable_declaration,
            $.variable_assignment,
            $.unary_expression,
            $.binary_expression,
            $.integer,
            $.rational,
            $.string,
            $.boolean,
            $.none,
            $.identifier,
            $.group,
            $.list,
        ),

        call: $ => prec(8, seq(
            field('function', $._expression),
            '(',
                sepBy(',', $._expression, 'argument'),
            ')',
        )),

        get_item: $ => prec(8, seq(
            field('left', $._expression),
            '[',
            field('index', $._expression),
            ']',
        )),

        variable_assignment: $ => seq(
            field('name', $.identifier),
            '=',
            field('value', $._expression),
        ),

        variable_declaration: $ => seq(
            field('name', $.identifier),
            ':',
            field('type', optional($._type)),
            '=',
            field('value', $._expression),
        ),

        unary_expression: $ => prec(7, choice(
            seq(field('operator', '-'), field('right', $._expression)),
            seq(field('operator', '!'), field('right', $._expression)),
        )),

        binary_expression: $ => {
            const operators = [
                [ 6, '*', ],
                [ 6, '/', ],
                [ 5, '+', ],
                [ 5, '-', ],
                [ 4, '>', ],
                [ 4, '>=', ],
                [ 3, '<', ],
                [ 3, '<=', ],
                [ 2, '==', ],
                [ 2, '!=', ],
                [ 1, 'or', ],
                [ 1, 'and', ],
            ];

            return choice(...operators.map(([precedence, operator]) => prec.left(precedence, seq(
                field('left', $._expression),
                field('operator', operator),
                field('right', $._expression),
            ))));
        },

        integer: $ => /\d+/,

        rational: $ => /\d+\.\d*/,

        string: $ => /"[^"]*"/,

        boolean: $ => choice(
            'true',
            'false',
        ),

        none: $ => 'none',

        identifier: $ => /[a-zA-Z_]+[a-zA-Z_0-9]*/,

        group: $ => seq(
            '(',
            field('expression', $._expression),
            ')',
        ),

        list: $ => seq(
            '[',
                sepBy(',', $._expression, 'value'),
            ']',
        ),

        _type: $ => choice(
            $.basic_type,
            $.func_type,
            $.list_type,
        ),

        basic_type: $ => choice(
            $.none,
            'int',
            'ratio',
            'bool',
            'str',
            'any',
        ),

        func_type: $ => seq(
            'func',
            '[',
                '[',
                    sepBy(',', $._type, 'parameter_type'),
                ']',
                ',',
                field('return_type', $._type),
            ']',
        ),

        list_type: $ => seq(
            'list',
            '[',
                field('element_type', $._type),
            ']',
        ),
    }
});

function sepBy(sep, rule, field_name) {
    return optional(seq(
        field(field_name, rule),
        repeat(seq(
            sep,
            field(field_name, rule),
        )),
    ))
}
