from app.jqqb.rule import Rule


class RuleGroup:
    def __init__(self, rule_group_dict):
        self.condition = rule_group_dict['condition']
        self.rules = rule_group_dict['rules']

    def evaluate(self, obj):
        if self.condition == 'AND':
            return all(map(lambda x: RuleGroup.get_rule_object(x).evaluate(obj), self.rules))
        else:
            return any(map(lambda x: RuleGroup.get_rule_object(x).evaluate(obj), self.rules))

    def get_field(self):
        l = list(map(lambda x: RuleGroup.get_rule_object(x).get_field(), self.rules))
        return list(set(self.flatten_list(l)))

    def get_field_value(self):
        l = list(map(lambda x: RuleGroup.get_rule_object(x).get_field_value(), self.rules))
        return self.flatten_list(l)

    def get_rules(self):
        l = list(map(lambda x: RuleGroup.get_rule_object(x).get_rules(), self.rules))
        return self.flatten_list(l)

    def get_values(self):
        l = list(map(lambda x: RuleGroup.get_rule_object(x).get_values(), self.rules))
        return self.flatten_list(l)

    @staticmethod
    def flatten_list(input_list):
        output_list = []

        for element in input_list:
            if isinstance(element, list):
                output_list.extend(RuleGroup.flatten_list(element))
            else:
                output_list.append(element)

        return output_list

    @staticmethod
    def get_rule_object(rule):
        if 'rules' in rule:
            return RuleGroup(rule)
        return Rule(rule)

    def format(self, variables):
        ...

    def find_params(self):
        ...